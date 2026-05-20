"""Speech service."""

from app.core.config import settings
from app.integrations.speech_client import MockSpeechClient, SpeechClient, TencentSpeechClient
from app.utils.logging import get_logger


logger = get_logger(__name__)


class SpeechService:
    """Speech-to-text service."""

    def __init__(self, client: SpeechClient | None = None) -> None:
        self.client = client or self._build_client()

    async def transcribe(self, audio_url: str) -> str:
        text = await self.client.transcribe(audio_url)
        logger.info("Speech transcription completed", extra={"provider": settings.speech_provider})
        return text

    def _build_client(self) -> SpeechClient:
        provider = settings.speech_provider.strip().lower()
        if provider == "mock":
            return MockSpeechClient()
        if provider == "tencent":
            return TencentSpeechClient()
        raise ValueError("SPEECH_PROVIDER must be 'mock' or 'tencent'.")
