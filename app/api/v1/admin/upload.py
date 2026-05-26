"""Admin upload endpoints."""

from fastapi import APIRouter, Depends, UploadFile

from app.core.admin_auth import AdminPrincipal, require_admin
from app.core.dependencies import get_upload_service
from app.services.upload_service import UploadService


router = APIRouter()


@router.post("/upload")
def upload_admin_file(
    file: UploadFile,
    service: UploadService = Depends(get_upload_service),
    principal: AdminPrincipal = Depends(require_admin),
) -> dict[str, str]:
    _ = principal
    return service.create_upload(file)
