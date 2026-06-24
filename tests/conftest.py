import pytest

from app.core.config import settings
from app.core.resilience import reset_resilience_state
from app.core.traffic import reset_traffic_state


@pytest.fixture(autouse=True)
def isolate_mutable_settings():
    reset_resilience_state()
    reset_traffic_state()
    saved = {
        "auth_api_keys": settings.auth_api_keys,
        "allow_mock_providers_in_prod": settings.allow_mock_providers_in_prod,
        "admin_jwt_secret": settings.admin_jwt_secret,
        "user_jwt_secret": settings.user_jwt_secret,
        "user_jwt_expire_minutes": settings.user_jwt_expire_minutes,
        "user_refresh_token_expire_days": settings.user_refresh_token_expire_days,
        "auth_otp_mock_enabled": settings.auth_otp_mock_enabled,
        "auth_otp_cooldown_seconds": settings.auth_otp_cooldown_seconds,
        "app_debug": settings.app_debug,
        "app_env": settings.app_env,
        "chat_stream_fast_products_enabled": settings.chat_stream_fast_products_enabled,
        "chat_stream_fast_products_limit": settings.chat_stream_fast_products_limit,
        "chat_stream_fast_reply_max_tokens": settings.chat_stream_fast_reply_max_tokens,
        "chat_auth_rate_limit_per_minute": settings.chat_auth_rate_limit_per_minute,
        "chat_anon_rate_limit_per_minute": settings.chat_anon_rate_limit_per_minute,
        "chat_session_rate_limit_per_minute": settings.chat_session_rate_limit_per_minute,
        "chat_session_tokens_enabled": settings.chat_session_tokens_enabled,
        "chat_anon_session_ttl_hours": settings.chat_anon_session_ttl_hours,
        "chat_context_max_messages": settings.chat_context_max_messages,
        "chat_context_max_chars": settings.chat_context_max_chars,
        "cors_allowed_origins": settings.cors_allowed_origins,
        "cors_allow_credentials": settings.cors_allow_credentials,
        "external_purchase_feedback_mode": settings.external_purchase_feedback_mode,
        "feedback_delay_days": settings.feedback_delay_days,
        "ai_chat_actions_require_auth_in_prod": settings.ai_chat_actions_require_auth_in_prod,
        "ai_checkout_confirmation_required": settings.ai_checkout_confirmation_required,
        "ai_media_url_allowlist_enabled": settings.ai_media_url_allowlist_enabled,
        "ai_media_allowed_hosts": settings.ai_media_allowed_hosts,
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
    settings.admin_jwt_secret = "test-admin-secret"
    settings.user_jwt_secret = "test-user-secret"
    settings.auth_otp_mock_enabled = True
    settings.chat_stream_fast_products_enabled = True
    settings.chat_stream_fast_products_limit = 5
    settings.chat_stream_fast_reply_max_tokens = 220
    settings.chat_auth_rate_limit_per_minute = 0
    settings.chat_anon_rate_limit_per_minute = 0
    settings.chat_session_rate_limit_per_minute = 0
    settings.chat_session_tokens_enabled = False
    settings.chat_anon_session_ttl_hours = 24
    settings.chat_context_max_messages = 8
    settings.chat_context_max_chars = 6000
    settings.ai_chat_actions_require_auth_in_prod = True
    settings.ai_checkout_confirmation_required = True
    settings.ai_media_url_allowlist_enabled = False
    settings.ai_media_allowed_hosts = ""
    settings.embedding_provider = "mock"
    settings.llm_provider = "mock"
    settings.speech_provider = "mock"
    settings.upload_provider = "local"
    settings.vision_provider = "mock"
    yield
    for key, value in saved.items():
        setattr(settings, key, value)
    reset_resilience_state()
    reset_traffic_state()
