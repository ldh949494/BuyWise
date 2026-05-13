from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="ShopAgent Backend", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_debug: bool = Field(default=True, alias="APP_DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")

    mysql_host: str = Field(default="127.0.0.1", alias="MYSQL_HOST")
    mysql_port: int = Field(default=3306, alias="MYSQL_PORT")
    mysql_user: str = Field(default="shopagent", alias="MYSQL_USER")
    mysql_password: str = Field(default="shopagent", alias="MYSQL_PASSWORD")
    mysql_database: str = Field(default="shopagent", alias="MYSQL_DATABASE")
    sqlalchemy_echo: bool = Field(default=False, alias="SQLALCHEMY_ECHO")

    chroma_persist_directory: str = Field(
        default="./vector_store/chroma",
        alias="CHROMA_PERSIST_DIRECTORY",
    )
    llm_provider: str = Field(default="mock", alias="LLM_PROVIDER")

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
