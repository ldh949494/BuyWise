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
from app.schemas.chat import BundlePlan, ChatRequest, ProductCard, StructuredNeed
from app.schemas.guide_preferences import AppliedPreferences
from app.schemas.chat_stream import (
    ChatStreamDoneEventData,
    ChatStreamErrorEventData,
    ChatStreamMetaEventData,
    ChatStreamProductsEventData,
    ChatStreamStatusEventData,
    ChatStreamTokenEventData,
)
from app.services.guide_follow_up_stream_service import GuideFollowUpStreamService
from app.utils.logging import get_logger


logger = get_logger(__name__)


class ChatStreamRunner:
    def __init__(self, chat_service: Any) -> None:
        self.chat_service = chat_service

    async def generate_events(
        self,
        request: ChatRequest,
        db: Session,
        user_id: int | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        started_at = time.perf_counter()
        context = self._build_context(request, db, user_id)
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

    async def generate_guide_events(
        self,
        request: ChatRequest,
        db: Session,
        user_id: int | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        async for event in self._generate_with_handler(request, db, user_id, self._generate_guide_from_context):
            yield event

    async def generate_follow_up_events(
        self,
        request: ChatRequest,
        db: Session,
        user_id: int | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        async for event in self._generate_with_handler(request, db, user_id, self._generate_follow_up_from_context):
            yield event

    async def _generate_with_handler(
        self,
        request: ChatRequest,
        db: Session,
        user_id: int | None,
        handler: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        started_at = time.perf_counter()
        context = self._build_context(request, db, user_id)
        try:
            async for event in handler(context, request, db):
                yield event
            observe_chat_stream_done_latency(context["stream_path"], time.perf_counter() - context["started_at"])
            observe_chat_latency("sse", "success", time.perf_counter() - started_at)
        except RuntimeError:
            logger.exception("Streaming guide handling failed", extra={"session_id": context["session_id"]})
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

    def _build_context(self, request: ChatRequest, db: Session, user_id: int | None) -> dict[str, Any]:
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
            "user_id": user_id,
            "applied_preferences": AppliedPreferences(ignored_saved_preferences=request.ignore_saved_preferences),
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
        self._apply_preferences(context, request, need, db)
        async for event in self._stream_recommendation(context, need, db):
            yield event

    async def _generate_guide_from_context(
        self,
        context: dict[str, Any],
        request: ChatRequest,
        db: Session,
    ) -> AsyncIterator[dict[str, Any]]:
        yield self._event("meta", ChatStreamMetaEventData(session_id=context["session_id"]))
        yield self._event("status", ChatStreamStatusEventData(stage="intent", message="intent"))
        need = await self._extract_need(context, request)
        if need.need_clarify:
            context["stream_path"] = "guide_clarify"
            async for event in self._stream_clarify(context, need):
                yield event
            return
        self._apply_preferences(context, request, need, db)
        async for event in self._stream_recommendation(context, need, db):
            yield event

    async def _generate_follow_up_from_context(
        self,
        context: dict[str, Any],
        request: ChatRequest,
        db: Session,
    ) -> AsyncIterator[dict[str, Any]]:
        yield self._event("meta", ChatStreamMetaEventData(session_id=context["session_id"]))
        async for event in GuideFollowUpStreamService(self.chat_service, self._event).generate_events(context, request):
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
        yield self._event("products", self._products_payload(context, need, [], need_clarify=True))
        yield self._event("done", ChatStreamDoneEventData(reply=reply))

    async def _stream_recommendation(
        self,
        context: dict[str, Any],
        need: Any,
        db: Session,
    ) -> AsyncIterator[dict[str, Any]]:
        yield self._event("status", ChatStreamStatusEventData(stage="retrieval", message="retrieval"))
        top_products, bundle_plans = await self._recommendation_products(need, db)
        fallback_meta = self._record_fallback_meta(context, "full_rag")
        payload_products = self._bundle_products(bundle_plans) if bundle_plans else top_products
        yield self._event(
            "products",
            self._products_payload(
                context,
                need,
                payload_products,
                need_clarify=False,
                bundle_plans=bundle_plans,
                fallback_meta=fallback_meta,
            ),
        )
        yield self._event("status", ChatStreamStatusEventData(stage="generation", message="generation"))
        async for event in self._stream_generation(context, need, payload_products, bundle_plans=bundle_plans):
            yield event

    async def _recommendation_products(self, need: Any, db: Session) -> tuple[list[Any], list[BundlePlan]]:
        if self.chat_service._is_bundle_intent(need):
            return await self.chat_service._recommendation_results(need, db)
        return await self._rank_products(need, db), []

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
        yield self._event(
            "products",
            self._products_payload(context, need, top_products, need_clarify=False, fallback_meta=fallback_meta),
        )
        yield self._event("status", ChatStreamStatusEventData(stage="generation", message="generation"))
        async for event in self._stream_generation(context, need, top_products, concise=True):
            yield event

    async def _fast_product_results(self, context: dict[str, Any], need: Any, db: Session) -> tuple[list[Any], dict[str, Any]]:
        top_products = self._rank_fast_products(need, db)
        if top_products:
            fallback_meta = {"fallback_used": False, "fallback_stage": "fast_db", "result_quality": "exact"}
            return top_products, self._record_fallback_meta(context, "fast_db", fallback_meta)
        top_products = await self._rank_products(need, db)
        fallback_meta = self.chat_service._rag_fallback_meta()
        return top_products, self._record_fallback_meta(context, "fast_db_empty_fallback", fallback_meta)

    def _record_fallback_meta(
        self,
        context: dict[str, Any],
        stream_path: str,
        fallback_meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        fallback_meta = fallback_meta or self.chat_service._rag_fallback_meta()
        context["fallback_meta"] = fallback_meta
        context["stream_path"] = stream_path
        self._observe_first_products(context, stream_path)
        return fallback_meta

    async def _stream_generation(
        self,
        context: dict[str, Any],
        need: Any,
        top_products: list[Any],
        *,
        concise: bool = False,
        bundle_plans: list[BundlePlan] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        chunks = []
        try:
            async for chunk in self._stream_recommendation_reply(need, top_products, concise=concise, bundle_plans=bundle_plans):
                chunks.append(chunk)
                yield self._event("token", ChatStreamTokenEventData(text=chunk))
        except Exception as exc:
            if not self._is_recoverable_llm_failure(exc):
                raise
            reason = self._failure_reason(exc)
            count_llm_failure("recommendation", reason)
            async for event in self._stream_fallback(context, need, top_products, degraded_reason=reason):
                yield event
            return
        reply = "".join(chunks)
        self._save_assistant(context, reply, need, top_products, need_clarify=False, bundle_plans=bundle_plans)
        yield self._event("done", ChatStreamDoneEventData(reply=reply))

    async def _stream_recommendation_reply(
        self,
        need: Any,
        top_products: list[Any],
        *,
        concise: bool,
        bundle_plans: list[BundlePlan] | None = None,
    ) -> AsyncIterator[str]:
        if bundle_plans:
            yield self.chat_service._fallback_bundle_reply(bundle_plans)
            return
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
        *,
        degraded_reason: str = "llm_capacity_limited",
    ) -> AsyncIterator[dict[str, Any]]:
        reply = self.chat_service._fallback_recommendation_reply(top_products)
        self._save_assistant(
            context,
            reply,
            need,
            top_products,
            need_clarify=False,
            degraded_reason=degraded_reason,
        )
        yield self._event("status", ChatStreamStatusEventData(stage="fallback", message=degraded_reason))
        yield self._event(
            "done",
            ChatStreamDoneEventData(reply=reply, degraded=True, degraded_reason=degraded_reason),
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
        bundle_plans: list[BundlePlan] | None = None,
    ) -> None:
        chat_repo = context["chat_repo"]
        structured_data = {"need": self.chat_service._dump(need), "need_clarify": need_clarify}
        structured_data["applied_preferences"] = self.chat_service._dump(context.get("applied_preferences") or AppliedPreferences())
        if products:
            structured_data["products"] = [self.chat_service._dump(product) for product in products]
        if bundle_plans:
            structured_data["bundle_plans"] = [self.chat_service._dump(plan) for plan in bundle_plans]
        fallback_meta = None if need_clarify else context.get("fallback_meta")
        if fallback_meta is None and not need_clarify:
            fallback_meta = self.chat_service._rag_fallback_meta()
        for key in ["fallback_used", "fallback_stage", "result_quality"]:
            if fallback_meta and key in fallback_meta:
                structured_data[key] = fallback_meta[key]
        if degraded_reason:
            structured_data["degraded"] = True
            structured_data["degraded_reason"] = degraded_reason
        chat_repo.create_message(context["session_id"], "assistant", reply, structured_data=structured_data)
        chat_repo.create_recommendations(context["session_id"], products)
        self.chat_service._commit(chat_repo)

    def _products_payload(
        self,
        context: dict[str, Any],
        need: Any,
        products: list[Any],
        *,
        need_clarify: bool,
        bundle_plans: list[BundlePlan] | None = None,
        fallback_meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        fallback_meta = fallback_meta or {"fallback_used": False, "fallback_stage": None, "result_quality": "exact"}
        return ChatStreamProductsEventData(
            need_clarify=need_clarify,
            structured_need=StructuredNeed.model_validate(self.chat_service._dump(need)),
            items=[ProductCard.model_validate(self.chat_service._dump(product)) for product in products],
            bundle_plans=bundle_plans or [],
            applied_preferences=context.get("applied_preferences") or AppliedPreferences(),
            fallback_used=bool(fallback_meta.get("fallback_used")),
            fallback_stage=fallback_meta.get("fallback_stage"),
            result_quality=str(fallback_meta.get("result_quality") or "exact"),
        )

    def _apply_preferences(
        self,
        context: dict[str, Any],
        request: ChatRequest,
        need: Any,
        db: Session,
    ) -> None:
        context["applied_preferences"] = self.chat_service._apply_preferences(
            request,
            need,
            db,
            context.get("user_id"),
        )

    def _bundle_products(self, bundle_plans: list[BundlePlan]) -> list[Any]:
        return self.chat_service._flatten_bundle_plan_products(bundle_plans)

    def _event(self, event: str, data: Any) -> dict[str, Any]:
        if hasattr(data, "model_dump"):
            data = data.model_dump(mode="json")
        return {"event": event, "data": data}

    def _is_recoverable_llm_failure(self, exc: Exception) -> bool:
        return is_capacity_limited(exc, "llm") or getattr(exc, "code", None) == "provider_timeout"

    def _failure_reason(self, exc: Exception) -> str:
        if is_capacity_limited(exc, "llm"):
            return "llm_capacity_limited"
        code = str(getattr(exc, "code", "provider_failure"))
        return f"llm_{code}"
