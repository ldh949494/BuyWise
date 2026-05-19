from fastapi.testclient import TestClient

from app.core.config import Settings, settings
from app.main import create_app


def test_create_app_applies_cors_policy() -> None:
    settings.cors_allowed_origins = "https://app.example.com"
    settings.cors_allow_credentials = False

    response = TestClient(create_app()).options(
        "/api/v1/health",
        headers={
            "Origin": "https://app.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://app.example.com"


def test_production_config_validation_rejects_insecure_settings() -> None:
    config = Settings(
        app_env="prod",
        app_debug=True,
        mysql_password="change-me",
        auth_api_keys="api:change-me:upload:write",
        cors_allowed_origins="",
        llm_provider="openai",
        llm_api_key="change-me",
    )

    try:
        config.validate_production()
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected production validation to fail.")

    assert "APP_DEBUG" in message
    assert "AUTH_API_KEYS" in message
    assert "LLM_API_KEY" in message
