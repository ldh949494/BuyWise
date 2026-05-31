"""Middleware provider implementation."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Literal

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.responses import Response

from app.core.config import settings
from app.core.request_context import REQUEST_ID_HEADER, reset_request_id, set_request_id
from app.core.traffic import rate_limit_response

ProviderName = Literal["auth", "telemetry", "logging", "errors", "middleware"]


class MiddlewareProvider:
    name: ProviderName = "middleware"

    def register_middleware(self, app: FastAPI) -> None:
        logger = logging.getLogger("app.middleware")

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
        logger.exception("Unhandled request error", extra=self._request_log_extra(request, status_code))

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
        return {"method": request.method, "path": request.url.path, "status_code": status_code}
