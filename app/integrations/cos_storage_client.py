"""Tencent COS object storage integration."""

from __future__ import annotations

from typing import BinaryIO, Protocol
from urllib.parse import quote

from app.core.config import settings
from app.core.providers import AppError
from app.core.resilience import provider_policy, run_provider_call


class ObjectStorageClient(Protocol):
    def upload_fileobj(
        self,
        *,
        key: str,
        fileobj: BinaryIO,
        content_type: str,
    ) -> str:
        ...


class TencentCosStorageClient:
    def __init__(self, client=None) -> None:
        self.client = client or self._create_client()

    def upload_fileobj(
        self,
        *,
        key: str,
        fileobj: BinaryIO,
        content_type: str,
    ) -> str:
        self._validate_settings()
        run_provider_call(
            provider_policy("cos", "upload_fileobj"),
            lambda: self.client.put_object(
                Bucket=settings.cos_bucket,
                Body=fileobj,
                Key=key,
                ContentType=content_type,
            ),
        )
        return self._public_url(key)

    def _create_client(self):
        try:
            from qcloud_cos import CosConfig, CosS3Client
        except ImportError as exc:
            raise RuntimeError("cos-python-sdk-v5 is required for Tencent COS uploads") from exc

        self._validate_settings()
        config = CosConfig(
            Region=settings.cos_region,
            SecretId=settings.tencent_secret_id,
            SecretKey=settings.tencent_secret_key,
            Token=None,
            Scheme="https",
        )
        return CosS3Client(config)

    def _validate_settings(self) -> None:
        missing = [
            name
            for name, value in {
                "TENCENT_SECRET_ID": settings.tencent_secret_id,
                "TENCENT_SECRET_KEY": settings.tencent_secret_key,
                "COS_BUCKET": settings.cos_bucket,
                "COS_REGION": settings.cos_region,
            }.items()
            if not value
        ]
        if missing:
            raise AppError(
                "Tencent COS settings are not configured.",
                status_code=500,
                code="storage_provider_not_configured",
                extra={"missing": missing},
            )

    def _public_url(self, key: str) -> str:
        base_url = settings.upload_public_base_url.strip()
        if base_url:
            return f"{base_url.rstrip('/')}/{quote(key)}"
        return f"https://{settings.cos_bucket}.cos.{settings.cos_region}.myqcloud.com/{quote(key)}"
