"""Request-scoped context values."""

from __future__ import annotations

from contextvars import ContextVar, Token


REQUEST_ID_HEADER = "X-Request-ID"
_REQUEST_ID: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    return _REQUEST_ID.get()


def set_request_id(request_id: str) -> Token[str | None]:
    return _REQUEST_ID.set(request_id)


def reset_request_id(token: Token[str | None]) -> None:
    _REQUEST_ID.reset(token)
