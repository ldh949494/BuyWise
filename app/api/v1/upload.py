"""Upload API endpoints."""

from fastapi import APIRouter, Depends, UploadFile

from app.services.upload_service import UploadService


router = APIRouter()


def get_upload_service() -> UploadService:
    return UploadService()


@router.post("/upload")
def upload_file(
    file: UploadFile,
    service: UploadService = Depends(get_upload_service),
) -> dict[str, str]:
    return service.save(file)
