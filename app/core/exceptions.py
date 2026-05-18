"""Application exception types."""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Domain error that can be rendered as an API response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 400,
        code: str = "app_error",
        extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.extra = extra or {}
