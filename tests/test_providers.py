from fastapi import FastAPI

from app.core.providers import (
    AuthProvider,
    ErrorProvider,
    LoggingProvider,
    TelemetryProvider,
    get_provider,
)


def test_get_provider_returns_cross_cutting_providers() -> None:
    assert isinstance(get_provider("auth"), AuthProvider)
    assert isinstance(get_provider("telemetry"), TelemetryProvider)
    assert isinstance(get_provider("logging"), LoggingProvider)
    assert isinstance(get_provider("errors"), ErrorProvider)


def test_auth_provider_defaults_to_anonymous_context() -> None:
    auth = get_provider("auth")

    assert auth.get_current_principal() is None


def test_error_provider_registers_without_side_effect_error() -> None:
    app = FastAPI()
    errors = get_provider("errors")

    errors.register_exception_handlers(app)

    assert isinstance(app, FastAPI)
