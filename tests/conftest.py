import pytest

from app.core.config import settings


@pytest.fixture(autouse=True)
def isolate_mutable_settings():
    saved = {
        "auth_api_keys": settings.auth_api_keys,
        "app_debug": settings.app_debug,
        "app_env": settings.app_env,
        "cors_allowed_origins": settings.cors_allowed_origins,
        "cors_allow_credentials": settings.cors_allow_credentials,
        "feedback_delay_days": settings.feedback_delay_days,
        "llm_provider": settings.llm_provider,
        "mysql_password": settings.mysql_password,
        "request_max_bytes": settings.request_max_bytes,
        "review_imported_base_weight": settings.review_imported_base_weight,
        "review_verified_base_weight": settings.review_verified_base_weight,
        "review_weight_cap": settings.review_weight_cap,
    }
    settings.auth_api_keys = ""
    settings.llm_provider = "mock"
    yield
    for key, value in saved.items():
        setattr(settings, key, value)
