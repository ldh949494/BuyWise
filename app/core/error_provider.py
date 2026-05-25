"""Error rendering provider implementation."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.core.exceptions import AppError
from app.core.logging_utils import REDACTED_VALUE
from app.core.request_context import REQUEST_ID_HEADER, get_request_id


class ErrorProvider:
    name = "errors"

    def register_exception_handlers(self, app: FastAPI) -> None:
        from app.core.providers import get_logging_provider

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
            headers=exc.headers,
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
            extra={"errors": self._sanitize_validation_errors(exc.errors())},
        )

    def _unexpected_error_response(self, request: Request) -> JSONResponse:
        return self._error_response(
            request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
            code="internal_error",
        )

    def _log_unexpected_error(self, logger: Any, request: Request) -> None:
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

    def _sanitize_validation_errors(self, errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
        sanitized = []
        for error in errors:
            next_error = dict(error)
            loc = tuple(str(item) for item in next_error.get("loc", ()))
            if self._has_sensitive_location(loc) and "input" in next_error:
                next_error["input"] = REDACTED_VALUE
            sanitized.append(next_error)
        return sanitized

    def _has_sensitive_location(self, loc: tuple[str, ...]) -> bool:
        sensitive_parts = ("password", "token", "secret", "api_key", "authorization")
        return any(any(part in item.lower() for part in sensitive_parts) for item in loc)
