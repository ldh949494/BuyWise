import pytest

from app.core.config import settings


@pytest.fixture(autouse=True)
def isolate_mutable_settings():
    saved = {
        "auth_api_keys": settings.auth_api_keys,
        "allow_mock_providers_in_prod": settings.allow_mock_providers_in_prod,
        "app_debug": settings.app_debug,
        "app_env": settings.app_env,
        "cors_allowed_origins": settings.cors_allowed_origins,
        "cors_allow_credentials": settings.cors_allow_credentials,
        "external_purchase_feedback_mode": settings.external_purchase_feedback_mode,
        "feedback_delay_days": settings.feedback_delay_days,
        "embedding_provider": settings.embedding_provider,
        "llm_provider": settings.llm_provider,
        "mysql_password": settings.mysql_password,
        "readiness_token": settings.readiness_token,
        "request_max_bytes": settings.request_max_bytes,
        "review_imported_base_weight": settings.review_imported_base_weight,
        "review_verified_base_weight": settings.review_verified_base_weight,
        "review_weight_cap": settings.review_weight_cap,
        "speech_provider": settings.speech_provider,
        "upload_provider": settings.upload_provider,
        "vision_provider": settings.vision_provider,
    }
    settings.auth_api_keys = ""
    settings.embedding_provider = "mock"
    settings.llm_provider = "mock"
    settings.speech_provider = "mock"
    settings.upload_provider = "local"
    settings.vision_provider = "mock"
    yield
    for key, value in saved.items():
        setattr(settings, key, value)
