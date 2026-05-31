from app.core.config import Settings


def test_settings_exposes_typed_domain_views() -> None:
    settings = Settings(
        _env_file=None,
        MYSQL_HOST="localhost",
        MYSQL_USER="root",
        MYSQL_PASSWORD="root",
        MYSQL_DATABASE="buywise",
        LLM_PROVIDER="openai-compatible",
        LLM_BASE_URL="https://llm.example.com/v1",
        EMBEDDING_PROVIDER="openai-compatible",
        EMBEDDING_BASE_URL="",
        UPLOAD_PROVIDER="local",
        UPLOAD_ALLOWED_TYPES="image/png,audio/wav",
        AUTH_API_KEYS="tester:test-token:orders:read",
        READINESS_TOKEN="ready-token",
        CORS_ALLOWED_ORIGINS="http://localhost:3000",
        CHAT_RATE_LIMIT_PER_MINUTE=15,
    )

    assert settings.database.url == "mysql+pymysql://root:root@localhost:3306/buywise"
    assert settings.ai.llm_provider == "openai-compatible"
    assert settings.ai.embedding_base_url == "https://llm.example.com/v1"
    assert settings.upload.allowed_content_types == ("image/png", "audio/wav")
    assert settings.security.auth_api_keys["test-token"]["subject"] == "tester"
    assert settings.traffic.chat_rate_limit_per_minute == 15
