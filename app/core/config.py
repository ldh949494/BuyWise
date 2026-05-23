from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

AppEnv = Literal["dev", "test", "prod"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = Field(default="BuyWise Backend", validation_alias="APP_NAME")
    app_env: AppEnv = Field(default="dev", validation_alias="APP_ENV")
    app_port: int = Field(default=8000, validation_alias="APP_PORT")
    app_debug: bool = Field(default=True, validation_alias="APP_DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", validation_alias="API_V1_PREFIX")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    mysql_host: str = Field(default="127.0.0.1", validation_alias="MYSQL_HOST")
    mysql_port: int = Field(default=3306, validation_alias="MYSQL_PORT")
    mysql_user: str = Field(default="buywise", validation_alias="MYSQL_USER")
    mysql_password: str = Field(default="buywise", validation_alias="MYSQL_PASSWORD")
    mysql_database: str = Field(default="buywise", validation_alias="MYSQL_DATABASE")
    sqlalchemy_echo: bool = Field(default=False, validation_alias="SQLALCHEMY_ECHO")

    chroma_persist_dir: str = Field(
        default="./vector_store/chroma",
        validation_alias=AliasChoices("CHROMA_PERSIST_DIR", "CHROMA_PERSIST_DIRECTORY"),
    )
    chroma_product_collection: str = Field(
        default="buywise_products",
        validation_alias="CHROMA_PRODUCT_COLLECTION",
    )

    llm_base_url: str = Field(
        default="https://api.openai.com/v1",
        validation_alias="LLM_BASE_URL",
    )
    llm_api_key: str = Field(default="", validation_alias="LLM_API_KEY")
    llm_model: str = Field(default="gpt-4o-mini", validation_alias="LLM_MODEL")
    embedding_model: str = Field(
        default="text-embedding-3-small",
        validation_alias="EMBEDDING_MODEL",
    )
    tencent_secret_id: str = Field(default="", validation_alias="TENCENT_SECRET_ID")
    tencent_secret_key: str = Field(default="", validation_alias="TENCENT_SECRET_KEY")
    cos_bucket: str = Field(default="", validation_alias="COS_BUCKET")
    cos_region: str = Field(default="", validation_alias="COS_REGION")

    vision_provider: str = Field(default="mock", validation_alias="VISION_PROVIDER")
    vision_base_url: str = Field(default="", validation_alias="VISION_BASE_URL")
    vision_api_key: str = Field(default="", validation_alias="VISION_API_KEY")
    vision_model: str = Field(default="", validation_alias="VISION_MODEL")
    speech_provider: str = Field(default="mock", validation_alias="SPEECH_PROVIDER")
    tencent_asr_region: str = Field(default="ap-guangzhou", validation_alias="TENCENT_ASR_REGION")
    tencent_asr_engine_model_type: str = Field(
        default="16k_zh",
        validation_alias="TENCENT_ASR_ENGINE_MODEL_TYPE",
    )
    tencent_asr_voice_format: str = Field(default="", validation_alias="TENCENT_ASR_VOICE_FORMAT")
    llm_provider: str = Field(default="mock", validation_alias="LLM_PROVIDER")
    auth_api_keys: str = Field(default="", validation_alias="AUTH_API_KEYS")
    request_max_bytes: int = Field(default=20 * 1024 * 1024, validation_alias="REQUEST_MAX_BYTES")
    upload_provider: str = Field(default="local", validation_alias="UPLOAD_PROVIDER")
    upload_dir: str = Field(default="uploads", validation_alias="UPLOAD_DIR")
    upload_public_base_url: str = Field(default="", validation_alias="UPLOAD_PUBLIC_BASE_URL")
    upload_max_bytes: int = Field(default=10 * 1024 * 1024, validation_alias="UPLOAD_MAX_BYTES")
    upload_allowed_types: str = Field(
        default="image/png,image/jpeg,image/webp,image/gif,audio/wav,audio/mpeg,audio/mp4,audio/ogg",
        validation_alias="UPLOAD_ALLOWED_TYPES",
    )
    cors_allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173,http://10.0.2.2:8000",
        validation_alias="CORS_ALLOWED_ORIGINS",
    )
    cors_allow_credentials: bool = Field(default=False, validation_alias="CORS_ALLOW_CREDENTIALS")
    cors_allowed_methods: str = Field(default="GET,POST,OPTIONS", validation_alias="CORS_ALLOWED_METHODS")
    cors_allowed_headers: str = Field(default="Authorization,Content-Type,X-Request-ID", validation_alias="CORS_ALLOWED_HEADERS")
    demo_user_ref: str = Field(default="demo-user", validation_alias="DEMO_USER_REF")
    feedback_delay_days: int = Field(default=7, validation_alias="FEEDBACK_DELAY_DAYS")
    review_imported_base_weight: float = Field(default=1.0, validation_alias="REVIEW_IMPORTED_BASE_WEIGHT")
    review_verified_base_weight: float = Field(default=2.0, validation_alias="REVIEW_VERIFIED_BASE_WEIGHT")
    review_weight_cap: float = Field(default=3.0, validation_alias="REVIEW_WEIGHT_CAP")

    @property
    def chroma_persist_directory(self) -> str:
        return self.chroma_persist_dir

    @property
    def upload_allowed_content_types(self) -> tuple[str, ...]:
        return tuple(
            content_type.strip().lower()
            for content_type in self.upload_allowed_types.split(",")
            if content_type.strip()
        )

    @property
    def configured_auth_api_keys(self) -> dict[str, dict[str, object]]:
        keys = {}
        for raw_item in self.auth_api_keys.split(";"):
            item = raw_item.strip()
            if not item:
                continue
            subject, token, scopes = self._parse_auth_key(item)
            keys[token] = {"subject": subject, "scopes": scopes}
        return keys

    @property
    def cors_origins(self) -> list[str]:
        return self._split_csv(self.cors_allowed_origins)

    @property
    def cors_methods(self) -> list[str]:
        return self._split_csv(self.cors_allowed_methods)

    @property
    def cors_headers(self) -> list[str]:
        return self._split_csv(self.cors_allowed_headers)

    @property
    def database_url(self) -> str:
        return URL.create(
            "mysql+pymysql",
            username=self.mysql_user,
            password=self.mysql_password,
            host=self.mysql_host,
            port=self.mysql_port,
            database=self.mysql_database,
        ).render_as_string(hide_password=False)

    @property
    def effective_vision_base_url(self) -> str:
        return self.vision_base_url.strip() or self.llm_base_url

    @property
    def effective_vision_api_key(self) -> str:
        return self.vision_api_key.strip() or self.llm_api_key

    @property
    def effective_vision_model(self) -> str:
        return self.vision_model.strip() or self.llm_model

    def validate_production(self) -> None:
        if self.app_env != "prod":
            return
        errors = []
        if self.app_debug:
            errors.append("APP_DEBUG must be false in prod.")
        if not self.configured_auth_api_keys:
            errors.append("AUTH_API_KEYS must include at least one production API key.")
        if not self.cors_origins:
            errors.append("CORS_ALLOWED_ORIGINS must be explicit in prod.")
        if self.cors_allow_credentials and "*" in self.cors_origins:
            errors.append("CORS_ALLOWED_ORIGINS cannot be '*' when credentials are enabled.")
        if self._is_placeholder(self.mysql_password):
            errors.append("MYSQL_PASSWORD must not be a placeholder in prod.")
        if self.llm_provider != "mock" and self._is_placeholder(self.llm_api_key):
            errors.append("LLM_API_KEY must be set for non-mock LLM providers in prod.")
        if self._uses_external_multimodal_provider() and not self._has_public_upload_url():
            errors.append(
                "UPLOAD_PUBLIC_BASE_URL must be set, or UPLOAD_PROVIDER must be cos, "
                "when VISION_PROVIDER or SPEECH_PROVIDER is non-mock in prod."
            )
        if self._contains_placeholder_auth_key():
            errors.append("AUTH_API_KEYS must not contain placeholder tokens in prod.")
        if errors:
            raise ValueError("Invalid production configuration: " + " ".join(errors))

    def _parse_auth_key(self, item: str) -> tuple[str, str, tuple[str, ...]]:
        parts = item.split(":", 2)
        if len(parts) < 2:
            return "api-key", item, ()
        subject = parts[0].strip() or "api-key"
        token = parts[1].strip()
        scopes = tuple(scope.strip() for scope in parts[2].split(",") if scope.strip()) if len(parts) == 3 else ()
        return subject, token, scopes

    def _split_csv(self, value: str) -> list[str]:
        return [item.strip() for item in value.split(",") if item.strip()]

    def _contains_placeholder_auth_key(self) -> bool:
        return any(self._is_placeholder(token) for token in self.configured_auth_api_keys)

    def _uses_external_multimodal_provider(self) -> bool:
        return self.vision_provider.strip().lower() != "mock" or self.speech_provider.strip().lower() != "mock"

    def _has_public_upload_url(self) -> bool:
        return bool(self.upload_public_base_url.strip()) or self.upload_provider.strip().lower() == "cos"

    def _is_placeholder(self, value: str) -> bool:
        normalized = value.strip().lower()
        return (
            not normalized
            or "change-me" in normalized
            or normalized in {"placeholder", "test-placeholder"}
            or normalized.startswith("your-")
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
