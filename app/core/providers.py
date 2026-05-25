"""Unified providers for cross-cutting concerns."""

from __future__ import annotations

import logging
import sys
import time
import uuid
from logging.config import dictConfig
from typing import Any, Callable, Literal, Protocol, TypeAlias, cast

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.responses import Response

from app.core.exceptions import AppError
from app.core.config import settings
from app.core.auth_provider import AuthProvider, Principal, require_principal_dependency
from app.core.error_provider import ErrorProvider
from app.core.logging_utils import JsonFormatter
from app.core.request_context import (
    REQUEST_ID_HEADER,
    reset_request_id,
    set_request_id,
)
from app.core.traffic import rate_limit_response

try:
    from prometheus_fastapi_instrumentator import Instrumentator
except ImportError:  # pragma: no cover - dependency is installed in normal runtime.
    Instrumentator = None


ProviderName: TypeAlias = Literal["auth", "telemetry", "logging", "errors", "middleware"]


class Provider(Protocol):
    name: ProviderName


class LoggingProvider:
    name: ProviderName = "logging"

    def configure(self, level: str | None = None) -> None:
        log_level = (level or settings.log_level).upper()
        dictConfig(self._config(log_level))

    def get_logger(self, name: str) -> logging.Logger:
        return logging.getLogger(name)

    def _config(self, log_level: str) -> dict[str, Any]:
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": self._formatters(),
            "handlers": self._handlers(),
            "root": self._root_logger(log_level),
            "loggers": self._named_loggers(log_level),
        }

    def _formatters(self) -> dict[str, Any]:
        return {"json": {"()": JsonFormatter}}

    def _handlers(self) -> dict[str, Any]:
        return {
            "default": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "json",
            },
        }

    def _root_logger(self, log_level: str) -> dict[str, Any]:
        return {"handlers": ["default"], "level": log_level}

    def _named_loggers(self, log_level: str) -> dict[str, Any]:
        return {
            name: {"handlers": ["default"], "level": log_level, "propagate": False}
            for name in ["uvicorn", "uvicorn.error", "uvicorn.access"]
        }


class TelemetryProvider:
    name: ProviderName = "telemetry"

    def instrument(self, app: FastAPI) -> None:
        if Instrumentator is not None:
            Instrumentator().instrument(app).expose(app)


class MiddlewareProvider:
    name: ProviderName = "middleware"

    def register_middleware(self, app: FastAPI) -> None:
        logger = get_logging_provider().get_logger("app.middleware")

        @app.middleware("http")
        async def request_context_middleware(request: Request, call_next: Any) -> Response:
            request_id = self._request_id(request)
            token = self._bind_request_id(request, request_id)
            started_at = time.perf_counter()
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            try:
                size_response = self._request_size_response(request)
                if size_response is not None:
                    status_code = size_response.status_code
                    return size_response
                limited_response = rate_limit_response(request)
                if limited_response is not None:
                    status_code = limited_response.status_code
                    return limited_response
                response = await call_next(request)
                status_code = response.status_code
                return response
            except Exception:
                self._log_unhandled_request_error(logger, request, status_code)
                raise
            finally:
                self._finish_request(logger, request, started_at, status_code, locals().get("response"))
                reset_request_id(token)

    def _request_id(self, request: Request) -> str:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        return request_id.strip() or str(uuid.uuid4())

    def _bind_request_id(self, request: Request, request_id: str) -> Any:
        token = set_request_id(request_id)
        request.state.request_id = request_id
        return token

    def _request_size_response(self, request: Request) -> JSONResponse | None:
        content_length = request.headers.get("content-length")
        if content_length is None:
            return None
        try:
            request_bytes = int(content_length)
        except ValueError:
            return None
        if request_bytes <= settings.request_max_bytes:
            return None
        return JSONResponse(
            status_code=413,
            content={
                "detail": "Request body is too large.",
                "code": "request_too_large",
                "extra": {
                    "max_bytes": settings.request_max_bytes,
                    "request_id": getattr(request.state, "request_id", None),
                },
            },
            headers={REQUEST_ID_HEADER: request.state.request_id},
        )

    def _log_unhandled_request_error(self, logger: logging.Logger, request: Request, status_code: int) -> None:
        logger.exception(
            "Unhandled request error",
            extra=self._request_log_extra(request, status_code),
        )

    def _finish_request(
        self,
        logger: logging.Logger,
        request: Request,
        started_at: float,
        status_code: int,
        response: Response | None,
    ) -> None:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        extra = self._request_log_extra(request, status_code)
        logger.info("Request completed", extra={**extra, "duration_ms": duration_ms})
        if response is not None:
            response.headers[REQUEST_ID_HEADER] = request.state.request_id

    def _request_log_extra(self, request: Request, status_code: int) -> dict[str, Any]:
        return {
            "method": request.method,
            "path": request.url.path,
            "status_code": status_code,
        }


_PROVIDERS: dict[ProviderName, Provider] = {
    "auth": AuthProvider(),
    "telemetry": TelemetryProvider(),
    "logging": LoggingProvider(),
    "errors": ErrorProvider(),
    "middleware": MiddlewareProvider(),
}

def get_provider(name: ProviderName) -> Any:
    return _PROVIDERS[name]

def get_logging_provider() -> LoggingProvider:
    return cast(LoggingProvider, get_provider("logging"))

def get_telemetry_provider() -> TelemetryProvider:
    return cast(TelemetryProvider, get_provider("telemetry"))

def get_error_provider() -> ErrorProvider:
    return cast(ErrorProvider, get_provider("errors"))

def get_middleware_provider() -> MiddlewareProvider:
    return cast(MiddlewareProvider, get_provider("middleware"))

def get_auth_provider() -> AuthProvider:
    return cast(AuthProvider, get_provider("auth"))

def require_principal(required_scopes: tuple[str, ...] = ()) -> Callable[[Request], Principal]:
    return require_principal_dependency(get_auth_provider(), required_scopes)
