from app.core.config import Settings


def test_prod_requires_user_jwt_secret_and_non_mock_otp() -> None:
    settings = Settings(
        _env_file=None,
        APP_ENV="prod",
        APP_DEBUG=False,
        MYSQL_PASSWORD="secret",
        AUTH_API_KEYS="api:prod-token:upload:write",
        READINESS_TOKEN="ready-token",
        ADMIN_JWT_SECRET="admin-jwt-secret",
        ALLOW_MOCK_PROVIDERS_IN_PROD=True,
        LLM_PROVIDER="mock",
        VISION_PROVIDER="mock",
        SPEECH_PROVIDER="mock",
    )

    try:
        settings.validate_production()
    except ValueError as exc:
        message = str(exc)
    else:
        message = ""

    assert "USER_JWT_SECRET must be set in prod." in message
    assert "AUTH_OTP_MOCK_ENABLED must be false in prod." not in message


def test_prod_rejects_mock_otp_without_beta_mock_override() -> None:
    settings = Settings(
        _env_file=None,
        APP_ENV="prod",
        APP_DEBUG=False,
        MYSQL_PASSWORD="secret",
        AUTH_API_KEYS="api:prod-token:upload:write",
        READINESS_TOKEN="ready-token",
        ADMIN_JWT_SECRET="admin-jwt-secret",
        USER_JWT_SECRET="user-jwt-secret",
        AUTH_OTP_MOCK_ENABLED=True,
        ALLOW_MOCK_PROVIDERS_IN_PROD=False,
        LLM_PROVIDER="openai-compatible",
        LLM_API_KEY="llm-key",
        VISION_PROVIDER="llm",
        VISION_API_KEY="vision-key",
        EMBEDDING_PROVIDER="openai-compatible",
        EMBEDDING_API_KEY="embedding-key",
        SPEECH_PROVIDER="mock",
        CHAT_SESSION_TOKENS_ENABLED=True,
        AI_MEDIA_URL_ALLOWLIST_ENABLED=True,
    )

    try:
        settings.validate_production()
    except ValueError as exc:
        message = str(exc)
    else:
        message = ""

    assert "AUTH_OTP_MOCK_ENABLED must be false in prod." in message


def test_prod_allows_mock_otp_for_explicit_beta_mock_override() -> None:
    settings = Settings(
        _env_file=None,
        APP_ENV="prod",
        APP_DEBUG=False,
        MYSQL_PASSWORD="secret",
        AUTH_API_KEYS="api:prod-token:upload:write",
        READINESS_TOKEN="ready-token",
        ADMIN_JWT_SECRET="admin-jwt-secret",
        USER_JWT_SECRET="user-jwt-secret",
        AUTH_OTP_MOCK_ENABLED=True,
        ALLOW_MOCK_PROVIDERS_IN_PROD=True,
        LLM_PROVIDER="mock",
        VISION_PROVIDER="mock",
        EMBEDDING_PROVIDER="mock",
        SPEECH_PROVIDER="mock",
        CHAT_SESSION_TOKENS_ENABLED=True,
        AI_MEDIA_URL_ALLOWLIST_ENABLED=True,
    )

    settings.validate_production()
