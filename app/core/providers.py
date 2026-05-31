"""Unified providers for cross-cutting concerns."""

from __future__ import annotations

from typing import Any, Callable, Literal, Protocol, TypeAlias, cast

from fastapi import Request

from app.core.auth_provider import AuthProvider, Principal, require_principal_dependency
from app.core.exceptions import AppError
from app.core.error_provider import ErrorProvider
from app.core.logging_provider import JsonFormatter, LoggingProvider
from app.core.middleware_provider import MiddlewareProvider
from app.core.telemetry_provider import TelemetryProvider


ProviderName: TypeAlias = Literal["auth", "telemetry", "logging", "errors", "middleware"]


class Provider(Protocol):
    name: ProviderName


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
