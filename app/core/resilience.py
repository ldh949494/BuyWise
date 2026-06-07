"""Shared resilience policy for external providers."""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from typing import TypeVar

from app.core.config import settings
from app.core.metrics import count_provider_failure
from app.core.providers import AppError
from app.core.traffic import run_with_capacity, stream_with_capacity


class ProviderFailureReason(StrEnum):
    CAPACITY = "capacity"
    TIMEOUT = "timeout"
    CONFIGURATION = "configuration_error"
    PROVIDER = "provider_error"


ResultT = TypeVar("ResultT")
_CIRCUITS: dict[str, CircuitState] = {}


@dataclass(frozen=True)
class ResiliencePolicy:
    provider: str
    operation: str
    timeout_seconds: float
    max_attempts: int = 2
    retry_backoff_seconds: float = 0.05
    circuit_failure_threshold: int = 3
    circuit_reset_seconds: float = 30.0

    @property
    def degraded_reason(self) -> str:
        return f"{self.provider}_capacity_limited"

    @property
    def key(self) -> str:
        return f"{self.provider}:{self.operation}"


@dataclass
class CircuitState:
    failures: int = 0
    opened_until: float = 0.0

    def is_open(self, now: float) -> bool:
        return self.opened_until > now


def provider_policy(provider: str, operation: str | None = None) -> ResiliencePolicy:
    return ResiliencePolicy(
        provider=provider,
        operation=operation or provider,
        timeout_seconds=settings.ai_provider_timeout_seconds,
    )


async def run_provider_call_async(
    policy: ResiliencePolicy,
    operation: Callable[[], Awaitable[ResultT]],
    *,
    capacity_resource: str | None = None,
) -> ResultT:
    last_exc: Exception | None = None
    for attempt in range(1, policy.max_attempts + 1):
        try:
            _ensure_circuit_allows(policy)
            if capacity_resource is None:
                result = await asyncio.wait_for(operation(), timeout=policy.timeout_seconds)
            else:
                result = await run_with_capacity(
                    capacity_resource,
                    operation,
                    timeout_seconds=policy.timeout_seconds,
                )
            _record_success(policy)
            return result
        except Exception as exc:
            if _is_circuit_open_error(exc):
                raise
            last_exc = exc
            reason = _record_failure(policy, exc)
            if attempt >= policy.max_attempts or not _should_retry(reason):
                raise
            await asyncio.sleep(policy.retry_backoff_seconds * attempt)
    raise last_exc or RuntimeError("Provider call failed without an exception.")


def run_provider_call(policy: ResiliencePolicy, operation: Callable[[], ResultT]) -> ResultT:
    last_exc: Exception | None = None
    for attempt in range(1, policy.max_attempts + 1):
        try:
            _ensure_circuit_allows(policy)
            result = operation()
            _record_success(policy)
            return result
        except Exception as exc:
            if _is_circuit_open_error(exc):
                raise
            last_exc = exc
            reason = _record_failure(policy, exc)
            if attempt >= policy.max_attempts or not _should_retry(reason):
                raise
            time.sleep(policy.retry_backoff_seconds * attempt)
    raise last_exc or RuntimeError("Provider call failed without an exception.")


@asynccontextmanager
async def provider_stream(policy: ResiliencePolicy, *, capacity_resource: str | None = None) -> AsyncIterator[None]:
    try:
        _ensure_circuit_allows(policy)
        if capacity_resource is None:
            yield
        else:
            async with stream_with_capacity(capacity_resource, timeout_seconds=policy.timeout_seconds):
                yield
        _record_success(policy)
    except Exception as exc:
        if _is_circuit_open_error(exc):
            raise
        _record_failure(policy, exc)
        raise


def reset_resilience_state() -> None:
    _CIRCUITS.clear()


def classify_provider_failure(exc: Exception) -> ProviderFailureReason:
    if isinstance(exc, AppError) and exc.code == "capacity_limited":
        return ProviderFailureReason.CAPACITY
    if isinstance(exc, TimeoutError):
        return ProviderFailureReason.TIMEOUT
    if isinstance(exc, AppError) and exc.code in {
        "provider_circuit_open",
        "provider_timeout",
    }:
        return ProviderFailureReason.TIMEOUT if exc.code == "provider_timeout" else ProviderFailureReason.PROVIDER
    if isinstance(exc, (RuntimeError, ValueError, AppError)) and "configured" in str(exc).lower():
        return ProviderFailureReason.CONFIGURATION
    if _exception_name_contains(exc, "timeout"):
        return ProviderFailureReason.TIMEOUT
    return ProviderFailureReason.PROVIDER


def _ensure_circuit_allows(policy: ResiliencePolicy) -> None:
    state = _CIRCUITS.get(policy.key)
    if state is None or not state.is_open(time.monotonic()):
        return
    raise AppError(
        "External provider circuit is open.",
        status_code=503,
        code="provider_circuit_open",
        extra={"provider": policy.provider, "operation": policy.operation},
    )


def _record_success(policy: ResiliencePolicy) -> None:
    _CIRCUITS.pop(policy.key, None)


def _record_failure(policy: ResiliencePolicy, exc: Exception) -> ProviderFailureReason:
    reason = classify_provider_failure(exc)
    count_provider_failure(policy.provider, policy.operation, reason.value)
    if reason in {ProviderFailureReason.PROVIDER, ProviderFailureReason.TIMEOUT}:
        state = _CIRCUITS.setdefault(policy.key, CircuitState())
        state.failures += 1
        if state.failures >= policy.circuit_failure_threshold:
            state.opened_until = time.monotonic() + policy.circuit_reset_seconds
    return reason


def _should_retry(reason: ProviderFailureReason) -> bool:
    return reason in {ProviderFailureReason.TIMEOUT, ProviderFailureReason.PROVIDER}


def _is_circuit_open_error(exc: Exception) -> bool:
    return isinstance(exc, AppError) and exc.code == "provider_circuit_open"


def _exception_name_contains(exc: Exception, text: str) -> bool:
    names: list[str] = []
    current: Any = type(exc)
    while current is not None:
        names.append(current.__name__.lower())
        current = current.__base__
    return any(text in name for name in names)
