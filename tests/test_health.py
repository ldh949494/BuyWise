from fastapi import FastAPI

from app.api.v1.health import health_check
from app.core.config import settings
from app.main import create_app


def test_create_app_returns_fastapi_instance() -> None:
    app = create_app()

    assert isinstance(app, FastAPI)


def test_health_route_is_registered() -> None:
    app = create_app()
    paths = {route.path for route in app.routes}

    assert f"{settings.api_v1_prefix}/health" in paths


def test_health_check_payload() -> None:
    payload = health_check()

    assert payload.status == "ok"
    assert payload.service == "buywise-backend"


def test_api_v1_prefix_default() -> None:
    assert settings.api_v1_prefix == "/api/v1"
