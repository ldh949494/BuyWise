"""Unified providers for cross-cutting concerns."""

from __future__ import annotations

import logging
import sys
import time
import uuid
from logging.config import dictConfig
from typing import Any, Literal, Protocol, TypeAlias, cast

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from starlette.responses import Response

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging_utils import JsonFormatter
from app.core.request_context import (
    REQUEST_ID_HEADER,
    get_request_id,
    reset_request_id,
    set_request_id,
)

try:
    from prometheus_fastapi_instrumentator import Instrumentator
except ImportError:  # pragma: no cover - dependency is installed in normal runtime.
    Instrumentator = None


ProviderName: TypeAlias = Literal["auth", "telemetry", "logging", "errors", "middleware"]


class Provider(Protocol):
    name: ProviderName


class Principal:
    def __init__(self, subject: str, scopes: tuple[str, ...] = ()) -> None:
        self.subject = subject
        self.scopes = scopes


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


class ErrorProvider:
    name: ProviderName = "errors"

    def register_exception_handlers(self, app: FastAPI) -> None:
        logger = get_logging_provider().get_logger("app.errors")

        @app.exception_handler(AppError)
        async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
            return self._app_error_response(request, exc)

        @app.exception_handler(HTTPException)
        async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
            return self._http_error_response(request, exc)

        @app.exception_handler(RequestValidationError)
        async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
            return self._validation_error_response(request, exc)

        @app.exception_handler(Exception)
        async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
            self._log_unexpected_error(logger, request)
            return self._unexpected_error_response(request)

    def _app_error_response(self, request: Request, exc: AppError) -> JSONResponse:
        return self._error_response(
            request,
            status_code=exc.status_code,
            detail=exc.message,
            code=exc.code,
            extra=exc.extra,
        )

    def _http_error_response(self, request: Request, exc: HTTPException) -> JSONResponse:
        return self._error_response(
            request,
            status_code=exc.status_code,
            detail=str(exc.detail),
            code=self._http_error_code(exc.status_code),
            headers=exc.headers,
        )

    def _validation_error_response(self, request: Request, exc: RequestValidationError) -> JSONResponse:
        return self._error_response(
            request,
            status_code=422,
            detail="Request validation failed",
            code="validation_error",
            extra={"errors": exc.errors()},
        )

    def _unexpected_error_response(self, request: Request) -> JSONResponse:
        return self._error_response(
            request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
            code="internal_error",
        )

    def _log_unexpected_error(self, logger: logging.Logger, request: Request) -> None:
        logger.exception(
            "Unhandled application error",
            extra={"method": request.method, "path": request.url.path},
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
        request_id = self._response_request_id(request)
        response_headers = self._response_headers(headers, request_id)
        payload_extra = self._payload_extra(extra, request_id)
        return JSONResponse(
            status_code=status_code,
            content={"detail": detail, "code": code, "extra": payload_extra},
            headers=response_headers,
        )

    def _response_request_id(self, request: Request) -> str | None:
        return getattr(request.state, "request_id", None) or get_request_id()

    def _response_headers(self, headers: dict[str, str] | None, request_id: str | None) -> dict[str, str]:
        response_headers = dict(headers or {})
        if request_id:
            response_headers[REQUEST_ID_HEADER] = request_id
        return response_headers

    def _payload_extra(self, extra: dict[str, Any] | None, request_id: str | None) -> dict[str, Any]:
        payload_extra = dict(extra or {})
        if request_id:
            payload_extra["request_id"] = request_id
        return payload_extra

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
