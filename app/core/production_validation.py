"""Production configuration validation helpers."""

from __future__ import annotations

from typing import Any


def validate_production_settings(settings: Any) -> None:
    if settings.app_env != "prod":
        return
    errors = _production_base_errors(settings)
    errors.extend(_production_provider_errors(settings))
    if _contains_placeholder_auth_key(settings):
        errors.append("AUTH_API_KEYS must not contain placeholder tokens in prod.")
    if errors:
        raise ValueError("Invalid production configuration: " + " ".join(errors))


def _production_base_errors(settings: Any) -> list[str]:
    errors = []
    if settings.app_debug:
        errors.append("APP_DEBUG must be false in prod.")
    if not settings.configured_auth_api_keys:
        errors.append("AUTH_API_KEYS must include at least one production API key.")
    if not settings.cors_origins:
        errors.append("CORS_ALLOWED_ORIGINS must be explicit in prod.")
    if settings.cors_allow_credentials and "*" in settings.cors_origins:
        errors.append("CORS_ALLOWED_ORIGINS cannot be '*' when credentials are enabled.")
    _append_secret_errors(settings, errors)
    if settings.auth_otp_mock_enabled:
        errors.append("AUTH_OTP_MOCK_ENABLED must be false in prod.")
    if settings.external_purchase_feedback_mode not in {"delayed", "immediate"}:
        errors.append("EXTERNAL_PURCHASE_FEEDBACK_MODE must be 'delayed' or 'immediate'.")
    return errors


def _append_secret_errors(settings: Any, errors: list[str]) -> None:
    required = {
        "MYSQL_PASSWORD": settings.mysql_password,
        "READINESS_TOKEN": settings.readiness_token,
        "ADMIN_JWT_SECRET": settings.admin_jwt_secret,
        "USER_JWT_SECRET": settings.user_jwt_secret,
    }
    for name, value in required.items():
        if _is_placeholder(value):
            errors.append(f"{name} must be set in prod.")


def _production_provider_errors(settings: Any) -> list[str]:
    errors = []
    if not settings.allow_mock_providers_in_prod and settings.llm_provider == "mock":
        errors.append("LLM_PROVIDER must not be mock in prod.")
    if not settings.allow_mock_providers_in_prod and settings.vision_provider == "mock":
        errors.append("VISION_PROVIDER must not be mock in prod.")
    if not settings.allow_mock_providers_in_prod and settings.embedding_provider == "mock":
        errors.append("EMBEDDING_PROVIDER must not be mock in prod.")
    if settings.llm_provider != "mock" and _is_placeholder(settings.llm_api_key):
        errors.append("LLM_API_KEY must be set for non-mock LLM providers in prod.")
    if settings.vision_provider != "mock" and _is_placeholder(settings.effective_vision_api_key):
        errors.append("VISION_API_KEY or LLM_API_KEY must be set for non-mock vision providers in prod.")
    if settings.embedding_provider != "mock" and _is_placeholder(settings.effective_embedding_api_key):
        errors.append("EMBEDDING_API_KEY or LLM_API_KEY must be set for non-mock embedding providers in prod.")
    if settings.upload_provider == "cos":
        errors.extend(_cos_configuration_errors(settings))
    if _uses_external_multimodal_provider(settings) and not _has_public_upload_url(settings):
        errors.append(
            "UPLOAD_PUBLIC_BASE_URL must be set, or UPLOAD_PROVIDER must be cos, "
            "when VISION_PROVIDER or SPEECH_PROVIDER is non-mock in prod."
        )
    return errors


def _cos_configuration_errors(settings: Any) -> list[str]:
    required = {
        "TENCENT_SECRET_ID": settings.tencent_secret_id,
        "TENCENT_SECRET_KEY": settings.tencent_secret_key,
        "COS_BUCKET": settings.cos_bucket,
        "COS_REGION": settings.cos_region,
    }
    return [
        f"{name} must be set when UPLOAD_PROVIDER=cos in prod."
        for name, value in required.items()
        if _is_placeholder(value)
    ]


def _contains_placeholder_auth_key(settings: Any) -> bool:
    return any(_is_placeholder(token) for token in settings.configured_auth_api_keys)


def _uses_external_multimodal_provider(settings: Any) -> bool:
    return settings.vision_provider.strip().lower() != "mock" or settings.speech_provider.strip().lower() != "mock"


def _has_public_upload_url(settings: Any) -> bool:
    return bool(settings.upload_public_base_url.strip()) or settings.upload_provider.strip().lower() == "cos"


def _is_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    return (
        not normalized
        or "change-me" in normalized
        or normalized in {"placeholder", "test-placeholder"}
        or normalized.startswith("your-")
    )
