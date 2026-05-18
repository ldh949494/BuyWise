"""File upload service."""

from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.utils.logging import get_logger


logger = get_logger(__name__)


class UploadService:
    """Local upload service, replaceable with Tencent COS later."""

    def __init__(self, upload_dir: str | Path = "uploads") -> None:
        self.upload_dir = Path(upload_dir)

    def save(self, file: UploadFile) -> dict[str, str]:
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        suffix = Path(file.filename or "").suffix
        filename = f"{uuid4().hex}{suffix}"
        target = self.upload_dir / filename

        with target.open("wb") as output:
            shutil.copyfileobj(file.file, output)

        logger.info(
            "Upload saved",
            extra={"stored_filename": filename, "content_type": file.content_type},
        )
        return {"url": f"/uploads/{filename}", "filename": filename}
