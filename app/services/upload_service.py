"""File upload service."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import AppError
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


class UploadService:
    """Local upload service, replaceable with Tencent COS later."""

    def __init__(
        self,
        upload_dir: str | Path = "uploads",
        *,
        max_bytes: int | None = None,
        allowed_content_types: tuple[str, ...] | None = None,
    ) -> None:
        self.upload_dir = Path(upload_dir)
        self.max_bytes = max_bytes if max_bytes is not None else settings.upload_max_bytes
        self.allowed_content_types = allowed_content_types or settings.upload_allowed_content_types

    def save(self, file: UploadFile) -> dict[str, str]:
        suffix = self._validate_upload_metadata(file)
        upload_root = self._upload_root()
        filename = self._build_storage_name(suffix)
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
        return {"url": f"/uploads/{filename}", "filename": filename}

    def _write_file(self, file: UploadFile, target: Path) -> int:
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

    def _too_large_error(self) -> AppError:
        return AppError(
            "Uploaded file is too large.",
            status_code=413,
            code="upload_too_large",
            extra={"max_bytes": self.max_bytes},
        )

    def _validate_upload_metadata(self, file: UploadFile) -> str:
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

    def _build_storage_name(self, suffix: str) -> str:
        return f"{uuid4().hex}{suffix}"

    def _safe_target(self, upload_root: Path, filename: str) -> Path:
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
