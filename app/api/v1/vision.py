"""Vision API endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.dependencies import get_vision_service
from app.services.vision_service import VisionService


class VisionRecognizeRequest(BaseModel):
    image_url: str


router = APIRouter(prefix="/vision")


@router.post("/recognize")
async def recognize_image(
    request: VisionRecognizeRequest,
    service: VisionService = Depends(get_vision_service),
) -> dict:
    return await service.recognize(request.image_url)
