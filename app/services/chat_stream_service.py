"""Streaming chat orchestration."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.orm import Session

from app.schemas.chat import ChatRequest
from app.utils.logging import get_logger


logger = get_logger(__name__)


class ChatStreamRunner:
    def __init__(self, chat_service: Any) -> None:
        self.chat_service = chat_service

    async def generate_events(
        self,
        request: ChatRequest,
        db: Session,
    ) -> AsyncIterator[dict[str, Any]]:
        context = self._build_context(request, db)
        try:
            async for event in self._generate_from_context(context, request, db):
                yield event
        except RuntimeError:
            logger.exception("Streaming chat handling failed", extra={"session_id": context["session_id"]})
            self.chat_service._rollback(context["chat_repo"])
            yield self._event(
                "error",
                {"message": "chat_stream_failed", "session_id": context["session_id"]},
            )

    def _build_context(self, request: ChatRequest, db: Session) -> dict[str, Any]:
        chat_repo = self.chat_service._chat_repo(request, db)
        chat_session = chat_repo.get_or_create_session(
            request.session_id,
            title=self.chat_service._session_title(request),
        )
        return {
            "chat_repo": chat_repo,
            "session_id": chat_session.session_id or chat_repo.generate_session_id(),
        }

    async def _generate_from_context(
        self,
        context: dict[str, Any],
        request: ChatRequest,
        db: Session,
    ) -> AsyncIterator[dict[str, Any]]:
        yield self._event("meta", {"session_id": context["session_id"]})
        yield self._event("status", {"stage": "intent", "message": "intent"})
        need = await self._extract_need(context, request)
        if need.need_clarify:
            async for event in self._stream_clarify(context, need):
                yield event
            return
        async for event in self._stream_recommendation(context, need, db):
            yield event

    async def _extract_need(self, context: dict[str, Any], request: ChatRequest) -> Any:
        chat_repo = context["chat_repo"]
        session_id = context["session_id"]
        text = await self.chat_service._build_user_text(request)
        image_info = await self.chat_service._build_image_info(request)
        history_context = self.chat_service._load_history_context(chat_repo, session_id)
        self.chat_service._save_user_message(chat_repo, session_id, request, text, image_info)
        return await self.chat_service.intent_service.extract(
            text,
            image_info=image_info,
            history_context=history_context,
        )

    async def _stream_clarify(
        self,
        context: dict[str, Any],
        need: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        yield self._event("status", {"stage": "generation", "message": "generation"})
        chunks = []
        async for chunk in self.chat_service.llm_client.stream_clarify_question(need):
            chunks.append(chunk)
            yield self._event("token", {"text": chunk})
        reply = "".join(chunks)
        self._save_assistant(context, reply, need, [], need_clarify=True)
        yield self._event("products", self._products_payload(need, [], need_clarify=True))
        yield self._event("done", {"reply": reply})

    async def _stream_recommendation(
        self,
        context: dict[str, Any],
        need: Any,
        db: Session,
    ) -> AsyncIterator[dict[str, Any]]:
        yield self._event("status", {"stage": "retrieval", "message": "retrieval"})
        top_products = await self._rank_products(need, db)
        yield self._event("products", self._products_payload(need, top_products, need_clarify=False))
        yield self._event("status", {"stage": "generation", "message": "generation"})
        chunks = []
        async for chunk in self.chat_service.llm_client.stream_recommendation(need, top_products):
            chunks.append(chunk)
            yield self._event("token", {"text": chunk})
        reply = "".join(chunks)
        self._save_assistant(context, reply, need, top_products, need_clarify=False)
        yield self._event("done", {"reply": reply})

    async def _rank_products(self, need: Any, db: Session) -> list[Any]:
        products = await self.chat_service.rag_pipeline.search_products(need, db)
        return self.chat_service.recommend_service.rank(products, need)[:5]

    def _save_assistant(
        self,
        context: dict[str, Any],
        reply: str,
        need: Any,
        products: list[Any],
        *,
        need_clarify: bool,
    ) -> None:
        chat_repo = context["chat_repo"]
        structured_data = {"need": self.chat_service._dump(need), "need_clarify": need_clarify}
        if products:
            structured_data["products"] = [self.chat_service._dump(product) for product in products]
        chat_repo.create_message(context["session_id"], "assistant", reply, structured_data=structured_data)
        chat_repo.create_recommendations(context["session_id"], products)
        self.chat_service._commit(chat_repo)

    def _products_payload(self, need: Any, products: list[Any], *, need_clarify: bool) -> dict[str, Any]:
        return {
            "need_clarify": need_clarify,
            "structured_need": self.chat_service._dump(need),
            "items": [self.chat_service._dump(product) for product in products],
        }

    def _event(self, event: str, data: dict[str, Any]) -> dict[str, Any]:
        return {"event": event, "data": data}
