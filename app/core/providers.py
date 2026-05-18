"""Unified providers for cross-cutting concerns."""

from __future__ import annotations

import logging
import sys
import time
import uuid
from dataclasses import dataclass
from logging.config import dictConfig
from typing import Any, Literal, Protocol, TypeAlias, cast

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from starlette.responses import Response

from app.core.exceptions import AppError
from app.core.config import settings
from app.core.logging_utils import JsonFormatter
from app.core.request_context import REQUEST_ID_HEADER, get_request_id, reset_request_id, set_request_id

try:
    from prometheus_fastapi_instrumentator import Instrumentator
except ImportError:  # pragma: no cover - dependency is installed in normal runtime.
    Instrumentator = None


ProviderName: TypeAlias = Literal["auth", "telemetry", "logging", "errors", "middleware"]


class Provider(Protocol):
    name: ProviderName


@dataclass(frozen=True)
class Principal:
    subject: str
    scopes: tuple[str, ...] = ()


class LoggingProvider:
    name: ProviderName = "logging"

    def configure(self, level: str | None = None) -> None:
        log_level = (level or settings.log_level).upper()
        dictConfig(
            {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "json": {
                        "()": JsonFormatter,
                    },
                },
                "handlers": {
                    "default": {
                        "class": "logging.StreamHandler",
                        "stream": sys.stdout,
                        "formatter": "json",
                    },
                },
                "root": {
                    "handlers": ["default"],
                    "level": log_level,
                },
                "loggers": {
                    "uvicorn": {
                        "handlers": ["default"],
                        "level": log_level,
                        "propagate": False,
                    },
                    "uvicorn.error": {
                        "handlers": ["default"],
                        "level": log_level,
                        "propagate": False,
                    },
                    "uvicorn.access": {
                        "handlers": ["default"],
                        "level": log_level,
                        "propagate": False,
                    },
                },
            }
        )

    def get_logger(self, name: str) -> logging.Logger:
        return logging.getLogger(name)


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
            request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
            request_id = request_id.strip() or str(uuid.uuid4())
            token = set_request_id(request_id)
            request.state.request_id = request_id
            started_at = time.perf_counter()
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            try:
                response = await call_next(request)
                status_code = response.status_code
                return response
            except Exception:
                logger.exception(
                    "Unhandled request error",
                    extra={
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": status_code,
                    },
                )
                raise
            finally:
                duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
                logger.info(
                    "Request completed",
                    extra={
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": status_code,
                        "duration_ms": duration_ms,
                    },
                )
                if "response" in locals():
                    response.headers[REQUEST_ID_HEADER] = request_id
                reset_request_id(token)


class ErrorProvider:
    name: ProviderName = "errors"

    def register_exception_handlers(self, app: FastAPI) -> None:
        logger = get_logging_provider().get_logger("app.errors")

        @app.exception_handler(AppError)
        async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
            return self._error_response(
                request,
                status_code=exc.status_code,
                detail=exc.message,
                code=exc.code,
                extra=exc.extra,
            )

        @app.exception_handler(HTTPException)
        async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
            return self._error_response(
                request,
                status_code=exc.status_code,
                detail=str(exc.detail),
                code=self._http_error_code(exc.status_code),
                headers=exc.headers,
            )

        @app.exception_handler(RequestValidationError)
        async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
            return self._error_response(
                request,
                status_code=422,
                detail="Request validation failed",
                code="validation_error",
                extra={"errors": exc.errors()},
            )

        @app.exception_handler(Exception)
        async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
            logger.exception(
                "Unhandled application error",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                },
            )
            return self._error_response(
                request,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
                code="internal_error",
            )

    def _error_response(
        self,
        request: Request,
        *,
        status_code: int,
        detail: str,
        code: str,
        extra: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None) or get_request_id()
        response_headers = dict(headers or {})
        if request_id:
            response_headers[REQUEST_ID_HEADER] = request_id
        payload_extra = dict(extra or {})
        if request_id:
            payload_extra["request_id"] = request_id
        return JSONResponse(
            status_code=status_code,
            content={"detail": detail, "code": code, "extra": payload_extra},
            headers=response_headers,
        )

    def _http_error_code(self, status_code: int) -> str:
        if status_code == status.HTTP_404_NOT_FOUND:
            return "not_found"
        if status_code == status.HTTP_401_UNAUTHORIZED:
            return "unauthorized"
        if status_code == status.HTTP_403_FORBIDDEN:
            return "forbidden"
        return "http_error"


class AuthProvider:
    name: ProviderName = "auth"

    def get_current_principal(self) -> Principal | None:
        return None


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
