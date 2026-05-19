"""Upload API endpoints."""

from fastapi import APIRouter, Depends, UploadFile

from app.core.providers import Principal, require_principal
from app.services.upload_service import UploadService


router = APIRouter()


def get_upload_service() -> UploadService:
    return UploadService()


@router.post("/upload")
def upload_file(
    file: UploadFile,
    service: UploadService = Depends(get_upload_service),
    principal: Principal = Depends(require_principal(("upload:write",))),
) -> dict[str, str]:
    _ = principal
    return service.save(file)
