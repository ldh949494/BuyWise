"""Fast product streaming helpers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.product_repo import ProductRepository
from app.schemas.chat import ChatRequest, StructuredNeed
from app.schemas.chat_stream import ChatStreamStatusEventData


class ChatStreamFastPathMixin:
    async def _stream_fast_products(
        self,
        context: dict[str, Any],
        request: ChatRequest,
        db: Session,
    ) -> AsyncIterator[dict[str, Any]]:
        need = self._extract_fast_need(context, request)
        if need.category is None:
            self._apply_preferences(context, request, need, db)
            async for event in self._stream_recommendation(context, need, db):
                yield event
            return
        self._apply_preferences(context, request, need, db)

        yield self._event("status", ChatStreamStatusEventData(stage="retrieval", message="fast_products"))
        top_products, fallback_meta = await self._fast_product_results(context, need, db)
        yield self._fast_products_event(context, need, top_products, fallback_meta)
        yield self._event("status", ChatStreamStatusEventData(stage="generation", message="generation"))
        async for event in self._stream_generation(context, need, top_products, concise=True):
            yield event

    async def _stream_guide_fast_first(
        self,
        context: dict[str, Any],
        request: ChatRequest,
        db: Session,
    ) -> AsyncIterator[dict[str, Any]]:
        fast_need = self._extract_fast_need(context, request)
        if fast_need.category is not None:
            self._apply_preferences(context, request, fast_need, db)
            fast_products = self._rank_fast_products(fast_need, db)
            if fast_products:
                for event in self._guide_fast_product_events(context, fast_need, fast_products):
                    yield event

        need = await self._extract_need(context, request)
        need = self._guide_final_need(need, fast_need)
        if need.need_clarify:
            context["stream_path"] = "guide_clarify"
            async for event in self._stream_clarify(context, need):
                yield event
            return
        self._apply_preferences(context, request, need, db)
        async for event in self._stream_recommendation(context, need, db):
            yield event

    def _fast_products_event(
        self,
        context: dict[str, Any],
        need: Any,
        top_products: list[Any],
        fallback_meta: dict[str, Any],
    ) -> dict[str, Any]:
        source = "fast_db" if fallback_meta.get("fallback_stage") == "fast_db" else self._products_source(fallback_meta)
        return self._event(
            "products",
            self._products_payload(
                context,
                need,
                top_products,
                need_clarify=False,
                fallback_meta=fallback_meta,
                source=source,
            ),
        )

    def _guide_fast_product_events(
        self,
        context: dict[str, Any],
        fast_need: StructuredNeed,
        fast_products: list[Any],
    ) -> list[dict[str, Any]]:
        fallback_meta = self._record_fallback_meta(
            context,
            "guide_fast_db",
            {"fallback_used": False, "fallback_stage": "fast_db", "result_quality": "exact"},
        )
        context["guide_provisional_products"] = fast_products
        return [
            self._event("status", ChatStreamStatusEventData(stage="retrieval", message="fast_products")),
            self._event(
                "products",
                self._products_payload(
                    context,
                    fast_need,
                    fast_products,
                    need_clarify=False,
                    fallback_meta=fallback_meta,
                    provisional=True,
                    source="fast_db",
                ),
            ),
        ]

    async def _fast_product_results(
        self,
        context: dict[str, Any],
        need: Any,
        db: Session,
    ) -> tuple[list[Any], dict[str, Any]]:
        top_products = self._rank_fast_products(need, db)
        if top_products:
            fallback_meta = {"fallback_used": False, "fallback_stage": "fast_db", "result_quality": "exact"}
            return top_products, self._record_fallback_meta(context, "fast_db", fallback_meta)
        top_products = await self._rank_products(need, db)
        fallback_meta = self.chat_service._rag_fallback_meta()
        return top_products, self._record_fallback_meta(context, "fast_db_empty_fallback", fallback_meta)

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
        self._save_user_message_once(context, request, text, None)
        need = self.chat_service.intent_service.extract_by_rules(text, image_info=None, history_context=history_context)
        if need.category is not None:
            need.need_clarify = False
            need.missing_fields = []
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

    def _final_empty_products_fallback(
        self,
        context: dict[str, Any],
        fallback_meta: dict[str, Any],
    ) -> tuple[list[Any], dict[str, Any]]:
        provisional_products = context.get("guide_provisional_products") or []
        if not provisional_products:
            return [], fallback_meta
        fallback_meta = {
            "fallback_used": True,
            "fallback_stage": "fast_db_final_fallback",
            "result_quality": "broad",
        }
        context["fallback_meta"] = fallback_meta
        context["stream_path"] = "guide_fast_db_final_fallback"
        return provisional_products, fallback_meta

    def _guide_final_need(self, need: Any, fast_need: StructuredNeed) -> Any:
        if not fast_need.category:
            return need
        if getattr(need, "category", None) is None:
            need.category = fast_need.category
        if getattr(need, "need_clarify", False) and getattr(need, "category", None):
            need.need_clarify = False
            need.missing_fields = []
        return need
