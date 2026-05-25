"""In-process traffic shaping helpers for closed beta capacity protection."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, TypeVar

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AppError


REQUEST_ID_HEADER = "X-Request-ID"


ResultT = TypeVar("ResultT")


class CapacityLimiter:
    """Small async limiter that fails fast when a resource is saturated."""

    def __init__(self, limit: int) -> None:
        self.limit = max(limit, 0)
        self._in_use = 0
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def acquire(self, resource: str) -> AsyncIterator[None]:
        if self.limit <= 0:
            yield
            return
        async with self._lock:
            if self._in_use >= self.limit:
                raise capacity_limited(resource)
            self._in_use += 1
        try:
            yield
        finally:
            async with self._lock:
                self._in_use = max(self._in_use - 1, 0)


class FixedWindowRateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str, *, limit: int, window_seconds: int) -> tuple[bool, int]:
        if limit <= 0:
            return True, 0
        now = time.monotonic()
        window_start = now - window_seconds
        hits = self._hits[key]
        while hits and hits[0] <= window_start:
            hits.popleft()
        if len(hits) >= limit:
            retry_after = max(int(window_seconds - (now - hits[0])) + 1, 1)
            return False, retry_after
        hits.append(now)
        return True, 0


@dataclass(frozen=True)
class EndpointLimit:
    scope: str
    per_minute: int


_RATE_LIMITER = FixedWindowRateLimiter()
_CAPACITY_LIMITERS: dict[str, CapacityLimiter] = {}


def rate_limit_response(request: Request) -> JSONResponse | None:
    endpoint_limit = _endpoint_limit(request.url.path)
    if endpoint_limit is None:
        return None
    identity = _rate_limit_identity(request)
    key = f"{endpoint_limit.scope}:{identity}"
    allowed, retry_after = _RATE_LIMITER.check(key, limit=endpoint_limit.per_minute, window_seconds=60)
    if allowed:
        return None
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "Too many requests.",
            "code": "rate_limited",
            "extra": {
                "limit_scope": endpoint_limit.scope,
                "retry_after_seconds": retry_after,
                "request_id": request_id,
            },
        },
        headers={
            "Retry-After": str(retry_after),
            REQUEST_ID_HEADER: request_id or "",
        },
    )


async def run_with_capacity(
    resource: str,
    operation: Callable[[], Awaitable[ResultT]],
    *,
    timeout_seconds: float | None = None,
) -> ResultT:
    async with capacity_limiter(resource).acquire(resource):
        try:
            return await asyncio.wait_for(operation(), timeout=_timeout(timeout_seconds))
        except TimeoutError as exc:
            raise provider_timeout(resource) from exc


@asynccontextmanager
async def stream_with_capacity(resource: str, *, timeout_seconds: float | None = None) -> AsyncIterator[None]:
    async with capacity_limiter(resource).acquire(resource):
        try:
            async with asyncio.timeout(_timeout(timeout_seconds)):
                yield
        except TimeoutError as exc:
            raise provider_timeout(resource) from exc


def capacity_limiter(resource: str) -> CapacityLimiter:
    limit = _resource_limit(resource)
    limiter = _CAPACITY_LIMITERS.get(resource)
    if limiter is None or limiter.limit != max(limit, 0):
        limiter = CapacityLimiter(limit)
        _CAPACITY_LIMITERS[resource] = limiter
    return limiter


def capacity_limited(resource: str) -> AppError:
    return AppError(
        "Service capacity is temporarily exhausted.",
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        code="capacity_limited",
        extra={"resource": resource, "retry_after_seconds": settings.capacity_retry_after_seconds},
        headers={"Retry-After": str(settings.capacity_retry_after_seconds)},
    )


def provider_timeout(resource: str) -> AppError:
    return AppError(
        "External provider timed out.",
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        code="provider_timeout",
        extra={"resource": resource},
    )


def is_capacity_limited(exc: BaseException, resource: str | None = None) -> bool:
    if not isinstance(exc, AppError) or exc.code != "capacity_limited":
        return False
    return resource is None or exc.extra.get("resource") == resource


def reset_traffic_state() -> None:
    _RATE_LIMITER._hits.clear()
    _CAPACITY_LIMITERS.clear()


def _endpoint_limit(path: str) -> EndpointLimit | None:
    if path.endswith("/ai/chat/stream") or path.endswith("/ai/chat"):
        return EndpointLimit("chat", settings.chat_rate_limit_per_minute)
    if "/vision" in path:
        return EndpointLimit("vision", settings.vision_rate_limit_per_minute)
    if "/speech" in path:
        return EndpointLimit("speech", settings.speech_rate_limit_per_minute)
    if path.endswith("/upload"):
        return EndpointLimit("upload", settings.upload_rate_limit_per_minute)
    return None


def _rate_limit_identity(request: Request) -> str:
    from app.core.providers import get_auth_provider

    principal = get_auth_provider().get_current_principal(request)
    if principal is not None:
        return f"subject:{principal.subject}"
    client_host = request.client.host if request.client else "unknown"
    return f"ip:{client_host}"


def _resource_limit(resource: str) -> int:
    if resource == "llm":
        return settings.ai_llm_max_concurrency
    if resource == "vision":
        return settings.ai_vision_max_concurrency
    if resource == "speech":
        return settings.ai_speech_max_concurrency
    return 0


def _timeout(timeout_seconds: float | None) -> float:
    value = settings.ai_provider_timeout_seconds if timeout_seconds is None else timeout_seconds
    return max(float(value), 0.1)
