"""Chat orchestration service."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.orm import Session

from app.ai.llm_client import LLMClient
from app.ai.rag_pipeline import RAGPipeline
from app.repositories.chat_repo import ChatRepository
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.intent_service import IntentService
from app.services.recommend_service import RecommendService
from app.services.speech_service import SpeechService
from app.services.vision_service import VisionService
from app.utils.logging import get_logger


logger = get_logger(__name__)


class NoopChatRepository:
    def __init__(self, session_id: str | None) -> None:
        self.session_id = session_id or "mock-session"

    def get_or_create_session(self, session_id: str | None = None, title: str | None = None):
        return type("ChatSessionStub", (), {"session_id": session_id or self.session_id})()

    def create_message(self, *args: Any, **kwargs: Any) -> None:
        return None

    def create_recommendations(self, *args: Any, **kwargs: Any) -> list[Any]:
        return []

    def list_messages(self, *args: Any, **kwargs: Any) -> list[Any]:
        return []

    def update_commit(self) -> None:
        return None

    def update_rollback(self) -> None:
        return None

    def generate_session_id(self) -> str:
        return self.session_id


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
        self.llm_client = llm_client or LLMClient()
        self.intent_service = intent_service or IntentService(llm_client=self.llm_client)
        self.rag_pipeline = rag_pipeline or RAGPipeline()
        self.recommend_service = recommend_service or RecommendService()

    async def handle_chat(self, request: ChatRequest, db: Session) -> ChatResponse:
        chat_repo = self._chat_repo(request, db)
        chat_session = chat_repo.get_or_create_session(request.session_id, title=self._session_title(request))
        session_id = chat_session.session_id or chat_repo.generate_session_id()

        try:
            text = await self._build_user_text(request)
            image_info = await self._build_image_info(request)
            history_context = self._load_history_context(chat_repo, session_id)
            self._save_user_message(chat_repo, session_id, request, text, image_info)

            need = await self.intent_service.extract(
                text,
                image_info=image_info,
                history_context=history_context,
            )

            if need.need_clarify:
                return await self._handle_clarify(chat_repo, session_id, need)
            return await self._handle_recommendation(chat_repo, session_id, need, db)
        except RuntimeError:
            logger.exception("Chat handling failed", extra={"session_id": session_id})
            self._rollback(chat_repo)
            return ChatResponse(
                reply="抱歉，当前暂时无法完成推荐，请稍后再试或换个条件。",
                need_clarify=False,
                structured_need=None,
                products=[],
                extra={"session_id": session_id},
            )

    def generate_chat_stream(self, request: ChatRequest, db: Session) -> AsyncIterator[dict[str, Any]]:
        from app.services.chat_stream_service import ChatStreamRunner

        return ChatStreamRunner(self).generate_events(request, db)

    async def _build_user_text(self, request: ChatRequest) -> str:
        text = request.message or ""
        if request.audio_url:
            audio_text = await self.speech_service.transcribe(request.audio_url)
            text = self._join_text(text, audio_text)
        return text

    async def _build_image_info(self, request: ChatRequest) -> dict | None:
        if not request.image_url:
            return None
        return await self.vision_service.recognize(request.image_url)

    def _load_history_context(self, chat_repo: Any, session_id: str) -> dict[str, Any]:
        prior_messages = chat_repo.list_messages(session_id)
        return self._history_context(prior_messages)

    def _save_user_message(
        self,
        chat_repo: Any,
        session_id: str,
        request: ChatRequest,
        text: str,
        image_info: dict | None,
    ) -> None:
        chat_repo.create_message(
            session_id,
            "user",
            text,
            structured_data={
                "image_url": request.image_url,
                "audio_url": request.audio_url,
                "image_info": image_info,
            },
        )

    async def _handle_clarify(self, chat_repo: Any, session_id: str, need: Any) -> ChatResponse:
        reply = await self.llm_client.generate_clarify_question(need)
        chat_repo.create_message(
            session_id,
            "assistant",
            reply,
            structured_data={"need": self._dump(need), "need_clarify": True},
        )
        self._commit(chat_repo)
        return ChatResponse(
            reply=reply,
            need_clarify=True,
            structured_need=need,
            products=[],
            extra={"session_id": session_id},
        )

    async def _handle_recommendation(
        self,
        chat_repo: Any,
        session_id: str,
        need: Any,
        db: Session,
    ) -> ChatResponse:
        products = await self.rag_pipeline.search_products(need, db)
        ranked_products = self.recommend_service.rank(products, need)
        top_products = ranked_products[:5]
        reply = await self.llm_client.generate_recommendation(need, top_products)

        chat_repo.create_message(
            session_id,
            "assistant",
            reply,
            structured_data={
                "need": self._dump(need),
                "products": [self._dump(product) for product in top_products],
            },
        )
        chat_repo.create_recommendations(session_id, top_products)
        self._commit(chat_repo)
        return ChatResponse(
            reply=reply,
            need_clarify=False,
            structured_need=need,
            products=top_products,
            extra={"session_id": session_id},
        )

    def _join_text(self, first: str, second: str) -> str:
        parts = [part.strip() for part in [first, second] if part and part.strip()]
        return "\n".join(parts)

    def _session_title(self, request: ChatRequest) -> str | None:
        if request.message:
            return request.message.strip()[:80]
        if request.image_url:
            return "Image shopping request"
        if request.audio_url:
            return "Audio shopping request"
        return None

    def _dump(self, value: Any) -> Any:
        if hasattr(value, "model_dump"):
            return value.model_dump(mode="json")
        return value

    def _commit(self, chat_repo: Any) -> None:
        db = getattr(chat_repo, "db", None)
        if db is not None:
            db.commit()

    def _rollback(self, chat_repo: Any) -> None:
        db = getattr(chat_repo, "db", None)
        if db is not None:
            db.rollback()

    def _chat_repo(self, request: ChatRequest, db: Session):
        if hasattr(db, "scalar") and hasattr(db, "add"):
            return ChatRepository(db)
        return NoopChatRepository(request.session_id)

    def _history_context(self, messages: list[Any]) -> dict[str, Any]:
        for message in reversed(messages):
            structured_data = getattr(message, "structured_data", None) or {}
            need = structured_data.get("need")
            if isinstance(need, dict):
                return {
                    key: need.get(key)
                    for key in ["category", "budget_max", "scenario", "preferences"]
                    if need.get(key) not in (None, [], "")
                }
        return {}
