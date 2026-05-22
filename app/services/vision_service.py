"""Vision service."""

from app.core.config import settings
from app.integrations.vision_client import LlmVisionClient, MockVisionClient, VisionClient
from app.utils.logging import get_logger


logger = get_logger(__name__)


class VisionService:
    """Vision recognition service."""

    def __init__(self, client: VisionClient | None = None) -> None:
        self.client = client or self._build_client()

    async def extract_image_info(self, image_url: str) -> dict:
        result = await self.client.recognize(image_url)
        logger.info(
            "Vision recognition completed",
            extra={
                "provider": settings.vision_provider,
                "category": result.get("category"),
                "feature_count": len(result.get("features") or []),
            },
        )
        return result

    def _build_client(self) -> VisionClient:
        provider = settings.vision_provider.strip().lower()
        if provider == "mock":
            return MockVisionClient()
        if provider in {"llm", "dashscope"}:
            return LlmVisionClient()
        raise ValueError("VISION_PROVIDER must be 'mock', 'llm', or 'dashscope'.")
