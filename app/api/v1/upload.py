"""Upload API endpoints."""

from fastapi import APIRouter, Depends, UploadFile

from app.core.dependencies import get_upload_service
from app.core.providers import Principal, require_principal
from app.services.upload_service import UploadService


router = APIRouter()


@router.post("/upload")
def upload_file(
    file: UploadFile,
    service: UploadService = Depends(get_upload_service),
    principal: Principal = Depends(require_principal(("upload:write",))),
) -> dict[str, str]:
    _ = principal
    return service.create_upload(file)
