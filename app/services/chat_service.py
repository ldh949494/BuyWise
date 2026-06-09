"""Chat orchestration service."""

from __future__ import annotations

from collections.abc import AsyncIterator
import time
from typing import Any

from sqlalchemy.orm import Session

from app.ai.llm_client import LLMClient
from app.ai.model_gateway import AIModelGateway
from app.ai.rag_pipeline import RAGPipeline
from app.core.metrics import count_llm_failure, observe_chat_latency
from app.core.traffic import is_capacity_limited
from app.core.transaction import UnitOfWork, unit_of_work
from app.repositories.chat_repo import ChatRepository
from app.repositories.price_repo import PriceHistoryRepository
from app.repositories.review_repo import ReviewRepository
from app.schemas.chat import BundlePlan, ChatRequest, ChatResponse
from app.schemas.guide_preferences import AppliedPreferences
from app.services.bundle_recommend_service import BundleRecommendService
from app.services.guide_preferences_service import GuidePreferencesService
from app.services.intent_service import IntentService
from app.services.noop_chat_repo import NoopChatRepository
from app.services.recommend_service import RecommendService
from app.services.speech_service import SpeechService
from app.services.vision_service import VisionService
from app.utils.logging import get_logger


logger = get_logger(__name__)


class ChatService:
    def __init__(
        self,
        speech_service: SpeechService | None = None,
        vision_service: VisionService | None = None,
        intent_service: IntentService | None = None,
        rag_pipeline: RAGPipeline | None = None,
        recommend_service: RecommendService | None = None,
        bundle_recommend_service: BundleRecommendService | None = None,
        llm_client: AIModelGateway | None = None,
    ) -> None:
        self.speech_service = speech_service or SpeechService()
        self.vision_service = vision_service or VisionService()
        self.llm_client = llm_client or LLMClient()
        self.intent_service = intent_service or IntentService(llm_client=self.llm_client)
        self.rag_pipeline = rag_pipeline or RAGPipeline()
        self.recommend_service = recommend_service or RecommendService()
        self.bundle_recommend_service = bundle_recommend_service or BundleRecommendService(self.recommend_service)

    async def handle_chat(self, request: ChatRequest, db: Session, user_id: int | None = None) -> ChatResponse:
        started_at = time.perf_counter()
        chat_repo = self._chat_repo(request, db)
        chat_session = chat_repo.get_or_create_session(request.session_id, title=self._session_title(request))
        session_id = chat_session.session_id or chat_repo.generate_session_id()

        try:
            response = await self._handle_chat_checked(request, chat_repo, session_id, db, user_id)
            self._observe_chat_response(response, started_at)
            return response
        except RuntimeError:
            logger.exception("Chat handling failed", extra={"session_id": session_id})
            self._rollback(chat_repo)
            observe_chat_latency("json", "error", time.perf_counter() - started_at)
        return ChatResponse(
            reply="抱歉，当前暂时无法完成推荐，请稍后再试或换个条件。",
            need_clarify=False,
            structured_need=None,
            products=[],
            bundle_plans=[],
            applied_preferences=AppliedPreferences(ignored_saved_preferences=request.ignore_saved_preferences),
            extra={"session_id": session_id},
        )

    async def _handle_chat_checked(
        self,
        request: ChatRequest,
        chat_repo: Any,
        session_id: str,
        db: Session,
        user_id: int | None,
    ) -> ChatResponse:
        text = await self._build_user_text(request)
        image_info = await self._build_image_info(request)
        history_context = self._load_history_context(chat_repo, session_id)
        self._save_user_message(chat_repo, session_id, request, text, image_info)
        need = await self._extract_need(text, image_info, history_context)
        if need.need_clarify:
            return await self._handle_clarify(chat_repo, session_id, need)
        applied_preferences = self._apply_preferences(request, need, db, user_id)
        return await self._handle_recommendation(chat_repo, session_id, need, db, applied_preferences)

    async def _extract_need(
        self,
        text: str,
        image_info: dict | None,
        history_context: dict[str, Any],
    ) -> Any:
        return await self.intent_service.extract(
            text,
            image_info=image_info,
            history_context=history_context,
        )

    def _observe_chat_response(self, response: ChatResponse, started_at: float) -> None:
        if response.need_clarify:
            outcome = "clarify"
        else:
            outcome = "degraded" if response.extra.get("degraded") else "success"
        observe_chat_latency("json", outcome, time.perf_counter() - started_at)

    def generate_chat_stream(
        self,
        request: ChatRequest,
        db: Session,
        user_id: int | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        from app.services.chat_stream_service import ChatStreamRunner

        return ChatStreamRunner(self).generate_events(request, db, user_id=user_id)

    def generate_guide_stream(
        self,
        request: ChatRequest,
        db: Session,
        user_id: int | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        from app.services.chat_stream_service import ChatStreamRunner

        return ChatStreamRunner(self).generate_guide_events(request, db, user_id=user_id)

    def generate_follow_up_stream(
        self,
        request: ChatRequest,
        db: Session,
        user_id: int | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        from app.services.chat_stream_service import ChatStreamRunner

        return ChatStreamRunner(self).generate_follow_up_events(request, db, user_id=user_id)

    async def _build_user_text(self, request: ChatRequest) -> str:
        text = request.message or ""
        if request.audio_url:
            audio_text = await self.speech_service.extract_transcript(request.audio_url)
            text = self._join_text(text, audio_text)
        return text

    async def _build_image_info(self, request: ChatRequest) -> dict | None:
        if not request.image_url:
            return None
        return await self.vision_service.extract_image_info(request.image_url)

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
        bundle_plans=[],
        applied_preferences=AppliedPreferences(),
        extra={"session_id": session_id},
    )

    async def _handle_recommendation(
        self,
        chat_repo: Any,
        session_id: str,
        need: Any,
        db: Session,
        applied_preferences: AppliedPreferences,
    ) -> ChatResponse:
        top_products, bundle_plans = await self._recommendation_results(need, db)
        reply, extra = await self._recommendation_reply(session_id, need, top_products, bundle_plans)
        chat_repo.create_message(
            session_id,
            "assistant",
            reply,
            structured_data=self._assistant_structured_data(need, top_products, extra, bundle_plans, applied_preferences),
        )
        chat_repo.create_recommendations(session_id, top_products)
        self._commit(chat_repo)
        return ChatResponse(
            reply=reply,
            need_clarify=False,
            structured_need=need,
            products=top_products,
            bundle_plans=bundle_plans,
            applied_preferences=applied_preferences,
            extra=extra,
        )

    async def _recommendation_reply(
        self,
        session_id: str,
        need: Any,
        top_products: list[Any],
        bundle_plans: list[BundlePlan] | None = None,
    ) -> tuple[str, dict[str, Any]]:
        extra: dict[str, Any] = {"session_id": session_id}
        if bundle_plans:
            return self._fallback_bundle_reply(bundle_plans), extra
        try:
            reply = await self.llm_client.generate_recommendation(need, top_products)
            return reply, extra
        except Exception as exc:
            if not is_capacity_limited(exc, "llm"):
                raise
            count_llm_failure("recommendation", "capacity_limited")
        extra.update({"degraded": True, "degraded_reason": "llm_capacity_limited"})
        return self._fallback_recommendation_reply(top_products), extra

    def _assistant_structured_data(
        self,
        need: Any,
        top_products: list[Any],
        extra: dict[str, Any],
        bundle_plans: list[BundlePlan] | None = None,
        applied_preferences: AppliedPreferences | None = None,
    ) -> dict[str, Any]:
        structured_data = {
            "need": self._dump(need),
            "products": [self._dump(product) for product in top_products],
            "applied_preferences": self._dump(applied_preferences or AppliedPreferences()),
        }
        if bundle_plans:
            structured_data["bundle_plans"] = [self._dump(plan) for plan in bundle_plans]
        if extra.get("degraded"):
            structured_data["degraded"] = True
            structured_data["degraded_reason"] = extra["degraded_reason"]
        return structured_data

    def _apply_preferences(
        self,
        request: ChatRequest,
        need: Any,
        db: Session,
        user_id: int | None,
    ) -> AppliedPreferences:
        if not hasattr(db, "scalar"):
            return AppliedPreferences(ignored_saved_preferences=request.ignore_saved_preferences)
        return GuidePreferencesService(db).build_applied_preferences(
            need,
            user_id=user_id,
            temporary_preferences=request.temporary_preferences,
            ignore_saved_preferences=request.ignore_saved_preferences,
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
            with unit_of_work(db):
                pass

    def _rollback(self, chat_repo: Any) -> None:
        db = getattr(chat_repo, "db", None)
        if db is not None:
            UnitOfWork(db).rollback()
    def _chat_repo(self, request: ChatRequest, db: Session):
        if hasattr(db, "scalar") and hasattr(db, "add"):
            return ChatRepository(db)
        return NoopChatRepository(request.session_id)

    def _fallback_recommendation_reply(self, products: list[Any]) -> str:
        if not products:
            return "暂时没有找到完全匹配的商品，可以放宽预算或调整条件。"
        names = "、".join(str(getattr(product, "name", "")) for product in products[:3] if getattr(product, "name", None))
        if names:
            return f"当前 AI 总结暂时繁忙，先为你返回基础推荐：{names}。你可以先查看商品卡片。"
        return "当前 AI 总结暂时繁忙，先为你返回基础推荐。你可以先查看商品卡片。"

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

    async def _rank_recommendations(self, need: Any, db: Session) -> list[Any]:
        if self._is_bundle_intent(need):
            return await self._rank_bundle_recommendations(need, db)
        strategy = self._get_need_value(need, "retrieval_strategy") or "balanced"
        products = await self.rag_pipeline.search_products(need, db, top_k=self._retrieval_top_k(strategy))
        self._attach_quality_signals(products, db)
        return self.recommend_service.rank(products, need)[: self._result_limit(strategy)]

    async def _recommendation_results(self, need: Any, db: Session) -> tuple[list[Any], list[BundlePlan]]:
        if not self._is_bundle_intent(need):
            return await self._rank_recommendations(need, db), []
        products = await self.rag_pipeline.search_products(need, db, top_k=30)
        self._attach_quality_signals(products, db)
        bundle_plans = self.bundle_recommend_service.build_plans(products, need)
        return self._flatten_bundle_plan_products(bundle_plans), bundle_plans

    async def _rank_bundle_recommendations(self, need: Any, db: Session) -> list[Any]:
        products = await self.rag_pipeline.search_products(need, db, top_k=30)
        self._attach_quality_signals(products, db)
        return self.bundle_recommend_service.rank_cards(products, need)

    def _is_bundle_intent(self, need: Any) -> bool:
        return self._get_need_value(need, "intent") in {"bundle_recommend", "场景化组合推荐"}

    def _flatten_bundle_plan_products(self, bundle_plans: list[BundlePlan]) -> list[Any]:
        products = []
        seen_ids = set()
        for plan in bundle_plans:
            for item in plan.items:
                if item.product.id in seen_ids:
                    continue
                seen_ids.add(item.product.id)
                products.append(item.product)
        return products

    def _fallback_bundle_reply(self, bundle_plans: list[BundlePlan]) -> str:
        names = "、".join(plan.title for plan in bundle_plans[:3])
        return f"我按预算档整理了 {len(bundle_plans)} 套组合方案：{names}。你可以先看总价、完整度和关键取舍，再进入方案对比。"

    def _get_need_value(self, need: Any, key: str) -> Any:
        if isinstance(need, dict):
            return need.get(key)
        return getattr(need, key, None)

    def _retrieval_top_k(self, strategy: str) -> int:
        if strategy == "explore":
            return 30
        if strategy == "strict":
            return 12
        return 20

    def _result_limit(self, strategy: str) -> int:
        if strategy == "explore":
            return 8
        return 5

    def _attach_quality_signals(self, products: list[Any], db: Session) -> None:
        if not hasattr(db, "execute"):
            return
        product_ids = [product.id for product in products]
        price_averages = PriceHistoryRepository(db).get_average_by_product_ids(product_ids)
        review_counts = ReviewRepository(db).get_sentiment_counts_by_product_ids(product_ids)
        for product in products:
            product.price_history_average = price_averages.get(product.id)
            product.review_sentiment_counts = review_counts.get(product.id, {})
