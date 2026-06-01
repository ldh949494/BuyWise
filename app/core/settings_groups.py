"""Typed settings domain views."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DatabaseSettings:
    url: str
    echo: bool
    chroma_persist_dir: str
    chroma_product_collection: str

    @classmethod
    def from_settings(cls, settings: Any) -> "DatabaseSettings":
        return cls(
            url=settings.database_url,
            echo=settings.sqlalchemy_echo,
            chroma_persist_dir=settings.chroma_persist_dir,
            chroma_product_collection=settings.chroma_product_collection,
        )


@dataclass(frozen=True)
class AISettings:
    llm_provider: str
    llm_base_url: str
    llm_model: str
    embedding_provider: str
    embedding_base_url: str
    embedding_model: str
    vision_provider: str
    speech_provider: str
    provider_timeout_seconds: float

    @classmethod
    def from_settings(cls, settings: Any) -> "AISettings":
        return cls(
            llm_provider=settings.llm_provider,
            llm_base_url=settings.llm_base_url,
            llm_model=settings.llm_model,
            embedding_provider=settings.embedding_provider,
            embedding_base_url=settings.effective_embedding_base_url,
            embedding_model=settings.embedding_model,
            vision_provider=settings.vision_provider,
            speech_provider=settings.speech_provider,
            provider_timeout_seconds=settings.ai_provider_timeout_seconds,
        )


@dataclass(frozen=True)
class UploadSettings:
    provider: str
    directory: str
    public_base_url: str
    max_bytes: int
    allowed_content_types: tuple[str, ...]

    @classmethod
    def from_settings(cls, settings: Any) -> "UploadSettings":
        return cls(
            provider=settings.upload_provider,
            directory=settings.upload_dir,
            public_base_url=settings.upload_public_base_url,
            max_bytes=settings.upload_max_bytes,
            allowed_content_types=settings.upload_allowed_content_types,
        )


@dataclass(frozen=True)
class SecuritySettings:
    auth_api_keys: dict[str, dict[str, object]]
    readiness_token: str
    admin_jwt_expire_minutes: int
    user_jwt_expire_minutes: int
    user_refresh_token_expire_days: int
    cors_origins: list[str]

    @classmethod
    def from_settings(cls, settings: Any) -> "SecuritySettings":
        return cls(
            auth_api_keys=settings.configured_auth_api_keys,
            readiness_token=settings.readiness_token,
            admin_jwt_expire_minutes=settings.admin_jwt_expire_minutes,
            user_jwt_expire_minutes=settings.user_jwt_expire_minutes,
            user_refresh_token_expire_days=settings.user_refresh_token_expire_days,
            cors_origins=settings.cors_origins,
        )


@dataclass(frozen=True)
class TrafficSettings:
    request_max_bytes: int
    chat_rate_limit_per_minute: int
    vision_rate_limit_per_minute: int
    speech_rate_limit_per_minute: int
    upload_rate_limit_per_minute: int

    @classmethod
    def from_settings(cls, settings: Any) -> "TrafficSettings":
        return cls(
            request_max_bytes=settings.request_max_bytes,
            chat_rate_limit_per_minute=settings.chat_rate_limit_per_minute,
            vision_rate_limit_per_minute=settings.vision_rate_limit_per_minute,
            speech_rate_limit_per_minute=settings.speech_rate_limit_per_minute,
            upload_rate_limit_per_minute=settings.upload_rate_limit_per_minute,
        )
