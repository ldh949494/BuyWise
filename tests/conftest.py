import pytest

from app.core.config import settings


@pytest.fixture(autouse=True)
def isolate_mutable_settings():
    saved = {
        "auth_api_keys": settings.auth_api_keys,
        "cors_allowed_origins": settings.cors_allowed_origins,
        "cors_allow_credentials": settings.cors_allow_credentials,
        "llm_provider": settings.llm_provider,
        "request_max_bytes": settings.request_max_bytes,
    }
    settings.auth_api_keys = ""
    settings.llm_provider = "mock"
    yield
    for key, value in saved.items():
        setattr(settings, key, value)
