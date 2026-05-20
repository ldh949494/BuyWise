"""File upload service."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Protocol
from urllib.parse import urljoin
from uuid import uuid4

from app.core.config import settings
from app.core.providers import AppError
from app.integrations.cos_storage_client import ObjectStorageClient, TencentCosStorageClient
from app.utils.logging import get_logger


logger = get_logger(__name__)
CHUNK_SIZE = 1024 * 1024
ALLOWED_EXTENSIONS_BY_TYPE = {
    "image/png": {".png"},
    "image/jpeg": {".jpg", ".jpeg"},
    "image/webp": {".webp"},
    "image/gif": {".gif"},
    "audio/wav": {".wav"},
    "audio/mpeg": {".mp3"},
    "audio/mp4": {".m4a"},
    "audio/ogg": {".ogg"},
}


class UploadInput(Protocol):
    filename: str | None
    content_type: str | None
    file: BinaryIO


class UploadService:
    """Local upload service, replaceable with Tencent COS later."""

    def __init__(
        self,
        upload_dir: str | Path | None = None,
        *,
        max_bytes: int | None = None,
        allowed_content_types: tuple[str, ...] | None = None,
        storage_client: ObjectStorageClient | None = None,
    ) -> None:
        self.upload_dir = Path(upload_dir or settings.upload_dir)
        self.max_bytes = max_bytes if max_bytes is not None else settings.upload_max_bytes
        self.allowed_content_types = allowed_content_types or settings.upload_allowed_content_types
        self.storage_client = storage_client

    def save(self, file: UploadInput) -> dict[str, str]:
        suffix = self._validate_upload_metadata(file)
        filename = self._build_storage_name(suffix)
        if self._upload_provider() == "cos":
            return self._save_to_cos(file, filename)

        upload_root = self._upload_root()
        target = self._safe_target(upload_root, filename)
        written = self._write_file(file, target)

        logger.info(
            "Upload saved",
            extra={
                "stored_filename": filename,
                "content_type": file.content_type,
                "bytes": written,
            },
        )
        return {"url": self._local_url(filename), "filename": filename}

    def _save_to_cos(self, file: UploadInput, filename: str) -> dict[str, str]:
        body, written = self._read_upload_to_memory(file)
        url = self._cos_storage_client().upload_fileobj(
            key=filename,
            fileobj=body,
            content_type=(file.content_type or "").lower(),
        )
        logger.info(
            "Upload saved",
            extra={
                "stored_filename": filename,
                "content_type": file.content_type,
                "bytes": written,
                "provider": "cos",
            },
        )
        return {"url": url, "filename": filename}

    def _write_file(self, file: UploadInput, target: Path) -> int:
        written = 0
        try:
            with target.open("wb") as output:
                while chunk := file.file.read(CHUNK_SIZE):
                    written += len(chunk)
                    if written > self.max_bytes:
                        raise self._too_large_error()
                    output.write(chunk)
        except Exception:
            if target.exists():
                target.unlink()
            raise
        return written

    def _read_upload_to_memory(self, file: UploadInput) -> tuple[BytesIO, int]:
        body = BytesIO()
        written = 0
        while chunk := file.file.read(CHUNK_SIZE):
            written += len(chunk)
            if written > self.max_bytes:
                raise self._too_large_error()
            body.write(chunk)
        body.seek(0)
        return body, written

    def _too_large_error(self) -> AppError:
        return AppError(
            "Uploaded file is too large.",
            status_code=413,
            code="upload_too_large",
            extra={"max_bytes": self.max_bytes},
        )

    def _validate_upload_metadata(self, file: UploadInput) -> str:
        suffix = Path(file.filename or "").suffix.lower()
        if not file.filename or not suffix:
            raise AppError(
                "Upload filename must include a supported extension.",
                status_code=400,
                code="invalid_upload_filename",
            )

        content_type = (file.content_type or "").lower()
        if content_type not in self.allowed_content_types:
            raise AppError(
                "Uploaded file type is not supported.",
                status_code=415,
                code="unsupported_upload_type",
                extra={"content_type": content_type},
            )

        allowed_extensions = ALLOWED_EXTENSIONS_BY_TYPE.get(content_type, set())
        if suffix not in allowed_extensions:
            raise AppError(
                "Uploaded file extension does not match the content type.",
                status_code=415,
                code="unsupported_upload_type",
                extra={"extension": suffix, "content_type": content_type},
            )
        return suffix

    def _upload_root(self) -> Path:
        upload_root = self.upload_dir.resolve()
        upload_root.mkdir(parents=True, exist_ok=True)
        return upload_root

    def _local_url(self, filename: str) -> str:
        relative_url = f"/uploads/{filename}"
        public_base_url = settings.upload_public_base_url.strip()
        if not public_base_url:
            return relative_url
        return urljoin(public_base_url.rstrip("/") + "/", relative_url.lstrip("/"))

    def _build_storage_name(self, suffix: str) -> str:
        return f"{uuid4().hex}{suffix}"

    def _safe_target(self, upload_root: Path, filename: str) -> Path:
        self.validate_storage_filename(filename)
        target = (upload_root / filename).resolve()
        try:
            target.relative_to(upload_root)
        except ValueError as exc:
            raise AppError(
                "Upload path is outside the upload directory.",
                status_code=400,
                code="unsafe_upload_path",
            ) from exc
        return target

    def _cos_storage_client(self) -> ObjectStorageClient:
        return self.storage_client or TencentCosStorageClient()

    def _upload_provider(self) -> str:
        provider = settings.upload_provider.strip().lower()
        if provider in {"local", "cos"}:
            return provider
        raise ValueError("UPLOAD_PROVIDER must be 'local' or 'cos'.")

    def validate_storage_filename(self, filename: str) -> str:
        path = Path(filename)
        suffix = path.suffix.lower()
        if path.name != filename:
            raise AppError(
                "Upload path is outside the upload directory.",
                status_code=400,
                code="unsafe_upload_path",
            )
        if filename.startswith(".") or not suffix:
            raise AppError(
                "Upload filename is not accessible.",
                status_code=400,
                code="invalid_upload_filename",
            )
        allowed_extensions = set().union(*ALLOWED_EXTENSIONS_BY_TYPE.values())
        if suffix not in allowed_extensions:
            raise AppError(
                "Uploaded file extension is not supported.",
                status_code=415,
                code="unsupported_upload_type",
                extra={"extension": suffix},
            )
        return filename
