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

    llm_provider: str = Field(default="mock", validation_alias="LLM_PROVIDER")

    @property
    def chroma_persist_directory(self) -> str:
        return self.chroma_persist_dir

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


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
