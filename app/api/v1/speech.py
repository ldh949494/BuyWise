"""Speech API endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.services.speech_service import SpeechService


class SpeechAsrRequest(BaseModel):
    audio_url: str


router = APIRouter(prefix="/speech")


def get_speech_service() -> SpeechService:
    return SpeechService()


@router.post("/asr")
async def transcribe_audio(
    request: SpeechAsrRequest,
    service: SpeechService = Depends(get_speech_service),
) -> dict[str, str]:
    return {"text": await service.transcribe(request.audio_url)}
