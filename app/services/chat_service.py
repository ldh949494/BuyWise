"""Chat orchestration service."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.llm_client import LLMClient
from app.ai.rag_pipeline import RAGPipeline
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.intent_service import IntentService
from app.services.recommend_service import RecommendService
from app.services.speech_service import SpeechService
from app.services.vision_service import VisionService


class ChatService:
    def __init__(
        self,
        speech_service: SpeechService | None = None,
        vision_service: VisionService | None = None,
        intent_service: IntentService | None = None,
        rag_pipeline: RAGPipeline | None = None,
        recommend_service: RecommendService | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        self.speech_service = speech_service or SpeechService()
        self.vision_service = vision_service or VisionService()
        self.intent_service = intent_service or IntentService()
        self.rag_pipeline = rag_pipeline or RAGPipeline()
        self.recommend_service = recommend_service or RecommendService()
        self.llm_client = llm_client or LLMClient()

    async def handle_chat(self, request: ChatRequest, db: Session) -> ChatResponse:
        try:
            text = request.message or ""
            if request.audio_url:
                audio_text = await self.speech_service.transcribe(request.audio_url)
                text = self._join_text(text, audio_text)

            image_info = None
            if request.image_url:
                image_info = await self.vision_service.recognize(request.image_url)

            need = await self.intent_service.extract(
                text,
                image_info=image_info,
                history_context=None,
            )

            if need.need_clarify:
                reply = await self.llm_client.generate_clarify_question(need)
                return ChatResponse(
                    reply=reply,
                    need_clarify=True,
                    structured_need=need,
                    products=[],
                )

            products = await self.rag_pipeline.search_products(need, db)
            ranked_products = self.recommend_service.rank(products, need)
            top_products = ranked_products[:5]
            reply = await self.llm_client.generate_recommendation(need, top_products)

            return ChatResponse(
                reply=reply,
                need_clarify=False,
                structured_need=need,
                products=top_products,
            )
        except Exception:
            return ChatResponse(
                reply="抱歉，当前暂时无法完成推荐，请稍后再试或换个条件。",
                need_clarify=False,
                structured_need=None,
                products=[],
            )

    def _join_text(self, first: str, second: str) -> str:
        parts = [part.strip() for part in [first, second] if part and part.strip()]
        return "\n".join(parts)
