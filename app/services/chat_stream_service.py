"""Streaming chat orchestration."""

from __future__ import annotations

from collections.abc import AsyncIterator
import time
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.metrics import (
    count_llm_failure,
    observe_chat_latency,
    observe_chat_stream_done_latency,
    observe_chat_stream_first_products_latency,
)
from app.core.traffic import is_capacity_limited
from app.repositories.product_repo import ProductRepository
from app.schemas.chat import ChatRequest, ProductCard, StructuredNeed
from app.schemas.chat_stream import (
    ChatStreamDoneEventData,
    ChatStreamErrorEventData,
    ChatStreamMetaEventData,
    ChatStreamProductsEventData,
    ChatStreamStatusEventData,
    ChatStreamTokenEventData,
)
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
        started_at = time.perf_counter()
        context = self._build_context(request, db)
        try:
            async for event in self._generate_from_context(context, request, db):
                yield event
            observe_chat_stream_done_latency(context["stream_path"], time.perf_counter() - context["started_at"])
            observe_chat_latency("sse", "success", time.perf_counter() - started_at)
        except RuntimeError:
            logger.exception("Streaming chat handling failed", extra={"session_id": context["session_id"]})
            self.chat_service._rollback(context["chat_repo"])
            observe_chat_latency("sse", "error", time.perf_counter() - started_at)
            yield self._event(
                "error",
                ChatStreamErrorEventData(
                    code="chat_stream_failed",
                    message="chat_stream_failed",
                    session_id=context["session_id"],
                ),
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
            "started_at": time.perf_counter(),
            "stream_path": "full_rag",
        }

    async def _generate_from_context(
        self,
        context: dict[str, Any],
        request: ChatRequest,
        db: Session,
    ) -> AsyncIterator[dict[str, Any]]:
        yield self._event("meta", ChatStreamMetaEventData(session_id=context["session_id"]))
        yield self._event("status", ChatStreamStatusEventData(stage="intent", message="intent"))
        if self._can_use_fast_products(request, db):
            async for event in self._stream_fast_products(context, request, db):
                yield event
            return
        need = await self._extract_need(context, request)
        if need.need_clarify:
            context["stream_path"] = "clarify"
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
        yield self._event("status", ChatStreamStatusEventData(stage="generation", message="generation"))
        chunks = []
        async for chunk in self.chat_service.llm_client.stream_clarify_question(need):
            chunks.append(chunk)
            yield self._event("token", ChatStreamTokenEventData(text=chunk))
        reply = "".join(chunks)
        self._save_assistant(context, reply, need, [], need_clarify=True)
        self._observe_first_products(context, context["stream_path"])
        yield self._event("products", self._products_payload(need, [], need_clarify=True))
        yield self._event("done", ChatStreamDoneEventData(reply=reply))

    async def _stream_recommendation(
        self,
        context: dict[str, Any],
        need: Any,
        db: Session,
    ) -> AsyncIterator[dict[str, Any]]:
        yield self._event("status", ChatStreamStatusEventData(stage="retrieval", message="retrieval"))
        top_products = await self._rank_products(need, db)
        context["stream_path"] = "full_rag"
        self._observe_first_products(context, "full_rag")
        yield self._event("products", self._products_payload(need, top_products, need_clarify=False))
        yield self._event("status", ChatStreamStatusEventData(stage="generation", message="generation"))
        async for event in self._stream_generation(context, need, top_products):
            yield event

    async def _stream_fast_products(
        self,
        context: dict[str, Any],
        request: ChatRequest,
        db: Session,
    ) -> AsyncIterator[dict[str, Any]]:
        need = self._extract_fast_need(context, request)
        if need.category is None:
            context["stream_path"] = "clarify"
            async for event in self._stream_clarify(context, need):
                yield event
            return

        yield self._event("status", ChatStreamStatusEventData(stage="retrieval", message="fast_products"))
        top_products = self._rank_fast_products(need, db)
        if not top_products:
            context["stream_path"] = "fast_db_empty_fallback"
            top_products = await self._rank_products(need, db)
            self._observe_first_products(context, "fast_db_empty_fallback")
        else:
            context["stream_path"] = "fast_db"
            self._observe_first_products(context, "fast_db")

        yield self._event("products", self._products_payload(need, top_products, need_clarify=False))
        yield self._event("status", ChatStreamStatusEventData(stage="generation", message="generation"))
        async for event in self._stream_generation(context, need, top_products, concise=True):
            yield event

    async def _stream_generation(
        self,
        context: dict[str, Any],
        need: Any,
        top_products: list[Any],
        *,
        concise: bool = False,
    ) -> AsyncIterator[dict[str, Any]]:
        chunks = []
        try:
            async for chunk in self._stream_recommendation_reply(need, top_products, concise=concise):
                chunks.append(chunk)
                yield self._event("token", ChatStreamTokenEventData(text=chunk))
        except Exception as exc:
            if not is_capacity_limited(exc, "llm"):
                raise
            count_llm_failure("recommendation", "capacity_limited")
            async for event in self._stream_fallback(context, need, top_products):
                yield event
            return
        reply = "".join(chunks)
        self._save_assistant(context, reply, need, top_products, need_clarify=False)
        yield self._event("done", ChatStreamDoneEventData(reply=reply))

    async def _stream_recommendation_reply(
        self,
        need: Any,
        top_products: list[Any],
        *,
        concise: bool,
    ) -> AsyncIterator[str]:
        if not concise:
            async for chunk in self.chat_service.llm_client.stream_recommendation(need, top_products):
                yield chunk
            return
        try:
            async for chunk in self.chat_service.llm_client.stream_recommendation(
                need,
                top_products,
                concise=True,
                max_tokens=settings.chat_stream_fast_reply_max_tokens,
            ):
                yield chunk
        except TypeError:
            async for chunk in self.chat_service.llm_client.stream_recommendation(need, top_products):
                yield chunk

    async def _stream_fallback(
        self,
        context: dict[str, Any],
        need: Any,
        top_products: list[Any],
    ) -> AsyncIterator[dict[str, Any]]:
        reply = self.chat_service._fallback_recommendation_reply(top_products)
        self._save_assistant(
            context,
            reply,
            need,
            top_products,
            need_clarify=False,
            degraded_reason="llm_capacity_limited",
        )
        yield self._event("status", ChatStreamStatusEventData(stage="fallback", message="llm_capacity_limited"))
        yield self._event(
            "done",
            ChatStreamDoneEventData(reply=reply, degraded=True, degraded_reason="llm_capacity_limited"),
        )

    async def _rank_products(self, need: Any, db: Session) -> list[Any]:
        return await self.chat_service._rank_recommendations(need, db)

    def _rank_fast_products(self, need: Any, db: Session) -> list[Any]:
        if not hasattr(db, "scalars"):
            return []
        products, _ = ProductRepository(db).list_products(
            category=need.category,
            price_max=need.budget_max,
            page=1,
            page_size=max(settings.chat_stream_fast_products_limit, 1),
        )
        return self.chat_service.recommend_service.rank(products, need)[: max(settings.chat_stream_fast_products_limit, 1)]

    def _extract_fast_need(self, context: dict[str, Any], request: ChatRequest) -> StructuredNeed:
        chat_repo = context["chat_repo"]
        session_id = context["session_id"]
        text = request.message or ""
        history_context = self.chat_service._load_history_context(chat_repo, session_id)
        self.chat_service._save_user_message(chat_repo, session_id, request, text, None)
        need = self.chat_service.intent_service.extract_by_rules(text, image_info=None, history_context=history_context)
        if need.category is not None:
            need.need_clarify = False
        return need

    def _can_use_fast_products(self, request: ChatRequest, db: Session) -> bool:
        return (
            settings.chat_stream_fast_products_enabled
            and bool((request.message or "").strip())
            and not request.image_url
            and not request.audio_url
            and hasattr(self.chat_service.intent_service, "extract_by_rules")
            and hasattr(db, "scalars")
            and self._has_no_prior_messages(request, db)
        )

    def _has_no_prior_messages(self, request: ChatRequest, db: Session) -> bool:
        if not request.session_id:
            return True
        chat_repo = self.chat_service._chat_repo(request, db)
        return not chat_repo.list_messages(request.session_id, limit=1)

    def _observe_first_products(self, context: dict[str, Any], path: str) -> None:
        if context.get("first_products_observed"):
            return
        context["first_products_observed"] = True
        observe_chat_stream_first_products_latency(path, time.perf_counter() - context["started_at"])

    def _save_assistant(
        self,
        context: dict[str, Any],
        reply: str,
        need: Any,
        products: list[Any],
        *,
        need_clarify: bool,
        degraded_reason: str | None = None,
    ) -> None:
        chat_repo = context["chat_repo"]
        structured_data = {"need": self.chat_service._dump(need), "need_clarify": need_clarify}
        if products:
            structured_data["products"] = [self.chat_service._dump(product) for product in products]
        if degraded_reason:
            structured_data["degraded"] = True
            structured_data["degraded_reason"] = degraded_reason
        chat_repo.create_message(context["session_id"], "assistant", reply, structured_data=structured_data)
        chat_repo.create_recommendations(context["session_id"], products)
        self.chat_service._commit(chat_repo)

    def _products_payload(self, need: Any, products: list[Any], *, need_clarify: bool) -> dict[str, Any]:
        return ChatStreamProductsEventData(
            need_clarify=need_clarify,
            structured_need=StructuredNeed.model_validate(self.chat_service._dump(need)),
            items=[ProductCard.model_validate(self.chat_service._dump(product)) for product in products],
        )

    def _event(self, event: str, data: Any) -> dict[str, Any]:
        if hasattr(data, "model_dump"):
            data = data.model_dump(mode="json")
        return {"event": event, "data": data}
