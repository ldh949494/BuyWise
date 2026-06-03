from app.core.config import Settings


def test_settings_reads_new_env_names() -> None:
    import os

    env = {
        "APP_NAME": "BuyWise",
        "APP_ENV": "prod",
        "APP_PORT": "9000",
        "MYSQL_HOST": "db.example.com",
        "MYSQL_PORT": "3307",
        "MYSQL_USER": "buyer",
        "MYSQL_PASSWORD": "secret",
        "MYSQL_DATABASE": "buywise",
        "CHROMA_PERSIST_DIR": "/var/lib/chroma",
        "CHROMA_PRODUCT_COLLECTION": "products_prod",
        "LLM_BASE_URL": "https://llm.example.com/v1",
        "LLM_API_KEY": "key-123",
        "LLM_MODEL": "gpt-4.1-mini",
        "EMBEDDING_MODEL": "text-embedding-3-large",
        "EMBEDDING_PROVIDER": "openai-compatible",
        "EMBEDDING_BASE_URL": "https://embedding.example.com/v1",
        "EMBEDDING_API_KEY": "embedding-key-123",
        "TENCENT_SECRET_ID": "sid",
        "TENCENT_SECRET_KEY": "skey",
        "COS_BUCKET": "bucket",
        "COS_REGION": "ap-shanghai",
        "VISION_PROVIDER": "llm",
        "VISION_BASE_URL": "https://vision.example.com/compatible-mode/v1",
        "VISION_API_KEY": "vision-key-123",
        "VISION_MODEL": "qwen-vl-plus",
        "SPEECH_PROVIDER": "tencent",
        "TENCENT_ASR_REGION": "ap-guangzhou",
        "TENCENT_ASR_ENGINE_MODEL_TYPE": "16k_zh",
        "TENCENT_ASR_VOICE_FORMAT": "wav",
        "READINESS_TOKEN": "ready-token",
        "ADMIN_JWT_SECRET": "admin-jwt-secret",
        "ADMIN_JWT_EXPIRE_MINUTES": "120",
        "USER_JWT_SECRET": "user-jwt-secret",
        "USER_JWT_EXPIRE_MINUTES": "15",
        "USER_REFRESH_TOKEN_EXPIRE_DAYS": "30",
        "AUTH_OTP_MOCK_ENABLED": "false",
        "ALLOW_MOCK_PROVIDERS_IN_PROD": "true",
        "EXTERNAL_PURCHASE_FEEDBACK_MODE": "immediate",
        "UPLOAD_PROVIDER": "cos",
        "UPLOAD_PUBLIC_BASE_URL": "https://cdn.example.com",
        "CHAT_STREAM_FAST_PRODUCTS_ENABLED": "false",
        "CHAT_STREAM_FAST_PRODUCTS_LIMIT": "7",
        "CHAT_STREAM_FAST_REPLY_MAX_TOKENS": "180",
    }
    previous = {key: os.environ.get(key) for key in env}
    os.environ.update(env)
    try:
        settings = Settings(_env_file=None)
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    assert settings.app_name == "BuyWise"
    assert settings.app_env == "prod"
    assert settings.app_port == 9000
    assert settings.mysql_host == "db.example.com"
    assert settings.mysql_port == 3307
    assert settings.mysql_user == "buyer"
    assert settings.mysql_password == "secret"
    assert settings.mysql_database == "buywise"
    assert settings.chroma_persist_dir == "/var/lib/chroma"
    assert settings.chroma_persist_directory == "/var/lib/chroma"
    assert settings.chroma_product_collection == "products_prod"
    assert settings.llm_base_url == "https://llm.example.com/v1"
    assert settings.llm_api_key == "key-123"
    assert settings.llm_model == "gpt-4.1-mini"
    assert settings.embedding_model == "text-embedding-3-large"
    assert settings.embedding_provider == "openai-compatible"
    assert settings.embedding_base_url == "https://embedding.example.com/v1"
    assert settings.embedding_api_key == "embedding-key-123"
    assert settings.effective_embedding_base_url == "https://embedding.example.com/v1"
    assert settings.effective_embedding_api_key == "embedding-key-123"
    assert settings.tencent_secret_id == "sid"
    assert settings.tencent_secret_key == "skey"
    assert settings.cos_bucket == "bucket"
    assert settings.cos_region == "ap-shanghai"
    assert settings.vision_provider == "llm"
    assert settings.vision_base_url == "https://vision.example.com/compatible-mode/v1"
    assert settings.vision_api_key == "vision-key-123"
    assert settings.vision_model == "qwen-vl-plus"
    assert settings.effective_vision_base_url == "https://vision.example.com/compatible-mode/v1"
    assert settings.effective_vision_api_key == "vision-key-123"
    assert settings.effective_vision_model == "qwen-vl-plus"
    assert settings.speech_provider == "tencent"
    assert settings.tencent_asr_region == "ap-guangzhou"
    assert settings.tencent_asr_engine_model_type == "16k_zh"
    assert settings.tencent_asr_voice_format == "wav"
    assert settings.readiness_token == "ready-token"
    assert settings.admin_jwt_secret == "admin-jwt-secret"
    assert settings.admin_jwt_expire_minutes == 120
    assert settings.user_jwt_secret == "user-jwt-secret"
    assert settings.user_jwt_expire_minutes == 15
    assert settings.user_refresh_token_expire_days == 30
    assert settings.auth_otp_mock_enabled is False
    assert settings.allow_mock_providers_in_prod is True
    assert settings.external_purchase_feedback_mode == "immediate"
    assert settings.upload_provider == "cos"
    assert settings.upload_public_base_url == "https://cdn.example.com"
    assert settings.chat_stream_fast_products_enabled is False
    assert settings.chat_stream_fast_products_limit == 7
    assert settings.chat_stream_fast_reply_max_tokens == 180


def test_settings_database_url_uses_pymysql() -> None:
    import os

    env = {
        "MYSQL_HOST": "localhost",
        "MYSQL_PORT": "3306",
        "MYSQL_USER": "root",
        "MYSQL_PASSWORD": "root",
        "MYSQL_DATABASE": "buywise",
    }
    previous = {key: os.environ.get(key) for key in env}
    os.environ.update(env)
    try:
        settings = Settings(_env_file=None)
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    assert settings.database_url == "mysql+pymysql://root:root@localhost:3306/buywise"


def test_vision_settings_fall_back_to_llm_settings() -> None:
    import os

    env = {
        "LLM_BASE_URL": "https://llm.example.com/v1",
        "LLM_API_KEY": "llm-key",
        "LLM_MODEL": "deepseek-chat",
        "VISION_BASE_URL": "",
        "VISION_API_KEY": "",
        "VISION_MODEL": "",
    }
    previous = {key: os.environ.get(key) for key in env}
    os.environ.update(env)
    try:
        settings = Settings(_env_file=None)
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    assert settings.effective_vision_base_url == "https://llm.example.com/v1"
    assert settings.effective_vision_api_key == "llm-key"
    assert settings.effective_vision_model == "deepseek-chat"


def test_embedding_settings_fall_back_to_llm_settings() -> None:
    import os

    env = {
        "LLM_BASE_URL": "https://llm.example.com/v1",
        "LLM_API_KEY": "llm-key",
        "EMBEDDING_BASE_URL": "",
        "EMBEDDING_API_KEY": "",
    }
    previous = {key: os.environ.get(key) for key in env}
    os.environ.update(env)
    try:
        settings = Settings(_env_file=None)
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    assert settings.effective_embedding_base_url == "https://llm.example.com/v1"
    assert settings.effective_embedding_api_key == "llm-key"


def test_settings_accepts_supported_app_env_values() -> None:
    import os

    previous = os.environ.get("APP_ENV")
    try:
        for app_env in ("dev", "test", "prod"):
            os.environ["APP_ENV"] = app_env
            assert Settings(_env_file=None).app_env == app_env
    finally:
        if previous is None:
            os.environ.pop("APP_ENV", None)
        else:
            os.environ["APP_ENV"] = previous


def test_settings_keeps_legacy_chroma_directory_alias() -> None:
    import os

    previous = os.environ.get("CHROMA_PERSIST_DIRECTORY")
    os.environ["CHROMA_PERSIST_DIRECTORY"] = "/tmp/legacy-chroma"
    try:
        settings = Settings(_env_file=None)
    finally:
        if previous is None:
            os.environ.pop("CHROMA_PERSIST_DIRECTORY", None)
        else:
            os.environ["CHROMA_PERSIST_DIRECTORY"] = previous

    assert settings.chroma_persist_dir == "/tmp/legacy-chroma"


def test_prod_non_mock_multimodal_requires_public_upload_url() -> None:
    settings = Settings(
        _env_file=None,
        APP_ENV="prod",
        APP_DEBUG=False,
        MYSQL_PASSWORD="secret",
        AUTH_API_KEYS="api:prod-token:upload:write",
        READINESS_TOKEN="ready-token",
        ADMIN_JWT_SECRET="admin-jwt-secret",
        USER_JWT_SECRET="user-jwt-secret",
        AUTH_OTP_MOCK_ENABLED=False,
        ALLOW_MOCK_PROVIDERS_IN_PROD=True,
        LLM_PROVIDER="mock",
        LLM_API_KEY="llm-key",
        VISION_PROVIDER="llm",
        SPEECH_PROVIDER="mock",
        UPLOAD_PROVIDER="local",
        UPLOAD_PUBLIC_BASE_URL="",
    )

    try:
        settings.validate_production()
    except ValueError as exc:
        message = str(exc)
    else:
        message = ""

    assert "UPLOAD_PUBLIC_BASE_URL must be set" in message


def test_prod_non_mock_multimodal_allows_cos_upload_provider() -> None:
    settings = Settings(
        _env_file=None,
        APP_ENV="prod",
        APP_DEBUG=False,
        MYSQL_PASSWORD="secret",
        AUTH_API_KEYS="api:prod-token:upload:write",
        READINESS_TOKEN="ready-token",
        ADMIN_JWT_SECRET="admin-jwt-secret",
        USER_JWT_SECRET="user-jwt-secret",
        AUTH_OTP_MOCK_ENABLED=False,
        ALLOW_MOCK_PROVIDERS_IN_PROD=True,
        LLM_PROVIDER="mock",
        VISION_PROVIDER="mock",
        SPEECH_PROVIDER="tencent",
        UPLOAD_PROVIDER="cos",
        TENCENT_SECRET_ID="sid",
        TENCENT_SECRET_KEY="skey",
        COS_BUCKET="bucket",
        COS_REGION="ap-shanghai",
    )

    settings.validate_production()


def test_prod_requires_non_mock_embedding_provider_by_default() -> None:
    settings = Settings(
        _env_file=None,
        APP_ENV="prod",
        APP_DEBUG=False,
        MYSQL_PASSWORD="secret",
        AUTH_API_KEYS="api:prod-token:upload:write",
        READINESS_TOKEN="ready-token",
        ADMIN_JWT_SECRET="admin-jwt-secret",
        USER_JWT_SECRET="user-jwt-secret",
        AUTH_OTP_MOCK_ENABLED=False,
        LLM_PROVIDER="openai-compatible",
        LLM_API_KEY="llm-key",
        VISION_PROVIDER="llm",
        UPLOAD_PROVIDER="cos",
        TENCENT_SECRET_ID="sid",
        TENCENT_SECRET_KEY="skey",
        COS_BUCKET="bucket",
        COS_REGION="ap-shanghai",
        EMBEDDING_PROVIDER="mock",
    )

    try:
        settings.validate_production()
    except ValueError as exc:
        message = str(exc)
    else:
        message = ""

    assert "EMBEDDING_PROVIDER must not be mock in prod." in message
