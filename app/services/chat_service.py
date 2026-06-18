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
from app.core.providers import Principal
from app.core.traffic import is_capacity_limited
from app.core.transaction import UnitOfWork, unit_of_work
from app.repositories.chat_repo import ChatRepository
from app.schemas.chat import BundlePlan, ChatRequest, ChatResponse
from app.schemas.guide_preferences import AppliedPreferences
from app.services.bundle_recommend_service import BundleRecommendService
from app.services.chat_action_service import ChatActionResult, ChatActionService
from app.services.chat_context_service import ChatContextService
from app.services.chat_recommendation_mixin import ChatRecommendationMixin
from app.services.chat_response_builders import (
    build_assistant_structured_data,
    build_chat_value_dump,
    build_fallback_recommendation_reply,
    build_out_of_scope_response,
    build_out_of_scope_reply,
    build_out_of_scope_structured_data,
    build_recommendation_response,
    build_security_extra,
    validate_out_of_scope_need,
)
from app.services.chat_session_security import ChatSessionContext, ChatSessionSecurityService
from app.services.chat_visual_search import handle_visual_search_request, validate_visual_search_request
from app.services.guide_preferences_service import GuidePreferencesService
from app.services.intent_service import IntentService
from app.services.media_url_policy import MediaUrlPolicy
from app.services.noop_chat_repo import NoopChatRepository
from app.services.order_service import get_current_user_ref
from app.services.recommend_service import RecommendService
from app.services.speech_service import SpeechService
from app.services.visual_search_service import VisualSearchService
from app.services.vision_service import VisionService
from app.utils.logging import get_logger


logger = get_logger(__name__)


class ChatService(ChatRecommendationMixin):
    def __init__(
        self,
        speech_service: SpeechService | None = None,
        vision_service: VisionService | None = None,
        intent_service: IntentService | None = None,
        rag_pipeline: RAGPipeline | None = None,
        recommend_service: RecommendService | None = None,
        bundle_recommend_service: BundleRecommendService | None = None,
        visual_search_service: VisualSearchService | None = None,
        chat_action_service: ChatActionService | None = None,
        llm_client: AIModelGateway | None = None,
    ) -> None:
        self.speech_service = speech_service or SpeechService()
        self.vision_service = vision_service or VisionService()
        self.llm_client = llm_client or LLMClient()
        self.intent_service = intent_service or IntentService(llm_client=self.llm_client)
        self.rag_pipeline = rag_pipeline or RAGPipeline()
        self.recommend_service = recommend_service or RecommendService()
        self.bundle_recommend_service = bundle_recommend_service or BundleRecommendService(self.recommend_service)
        self.visual_search_service = visual_search_service or VisualSearchService(
            vision_service=self.vision_service,
            rag_pipeline=self.rag_pipeline,
            recommend_service=self.recommend_service,
        )
        self.chat_action_service = chat_action_service or ChatActionService()
        self.chat_session_security = ChatSessionSecurityService()
        self.media_url_policy = MediaUrlPolicy()
        self.chat_context_service = ChatContextService()

    async def handle_chat(
        self,
        request: ChatRequest,
        db: Session,
        user_id: int | None = None,
        principal: Principal | None = None,
    ) -> ChatResponse:
        started_at = time.perf_counter()
        chat_repo = self._chat_repo(request, db)
        security_context = self._chat_security_context(request, chat_repo, principal, user_id)
        session_id = security_context.session_id

        try:
            response = await self._handle_chat_checked(request, chat_repo, security_context, db)
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
            extra=build_security_extra(security_context),
        )

    async def _handle_chat_checked(
        self,
        request: ChatRequest,
        chat_repo: Any,
        security_context: ChatSessionContext,
        db: Session,
    ) -> ChatResponse:
        session_id = security_context.session_id
        text = await self._build_user_text(request)
        image_info = await self._build_image_info(request)
        history_context = self._load_history_context(chat_repo, session_id)
        self._save_user_message(chat_repo, session_id, request, text, image_info)
        if action_result := self._execute_chat_action(text, chat_repo, security_context, db):
            return self._handle_action_result(chat_repo, security_context, action_result)
        if validate_visual_search_request(request, text):
            return await self._handle_visual_search(request, text, chat_repo, security_context, db)
        need = await self._extract_need(text, image_info, history_context)
        if self._is_out_of_scope_need(need):
            return self._handle_out_of_scope(chat_repo, security_context)
        if need.need_clarify:
            return await self._handle_clarify(chat_repo, security_context, need)
        applied_preferences = self._apply_preferences(request, need, db, security_context.user_id)
        return await self._handle_recommendation(chat_repo, security_context, need, db, applied_preferences)

    async def _handle_visual_search(
        self,
        request: ChatRequest,
        text: str,
        chat_repo: Any,
        security_context: ChatSessionContext,
        db: Session,
    ) -> ChatResponse:
        response = await handle_visual_search_request(
            request,
            text,
            chat_repo,
            security_context.session_id,
            db,
            self.visual_search_service,
            dump=self._dump,
        )
        response.extra.update(build_security_extra(security_context))
        return response

    def _execute_chat_action(
        self,
        text: str,
        chat_repo: Any,
        security_context: ChatSessionContext,
        db: Session,
    ) -> ChatActionResult | None:
        return self.chat_action_service.handle_if_action(
            text=text,
            chat_repo=chat_repo,
            session_id=security_context.session_id,
            db=db,
            user_ref=get_current_user_ref(security_context.owner_subject),
            owner_subject=security_context.owner_subject,
            owner_auth_type=security_context.owner_auth_type,
        )

    def _handle_action_result(
        self,
        chat_repo: Any,
        security_context: ChatSessionContext,
        action_result: ChatActionResult,
    ) -> ChatResponse:
        chat_repo.create_message(
            security_context.session_id,
            "assistant",
            action_result.reply,
            structured_data={"action": action_result.action, **action_result.data},
        )
        self._commit(chat_repo)
        return ChatResponse(
            reply=action_result.reply,
            need_clarify=False,
            structured_need=None,
            products=[],
            bundle_plans=[],
            applied_preferences=AppliedPreferences(),
            extra={
                **build_security_extra(security_context),
                "action": action_result.action,
                **action_result.data,
            },
        )

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

    def _is_out_of_scope_need(self, need: Any) -> bool:
        return validate_out_of_scope_need(need, self._get_need_value)

    def _handle_out_of_scope(self, chat_repo: Any, security_context: ChatSessionContext) -> ChatResponse:
        reply = self._out_of_scope_reply()
        chat_repo.create_message(
            security_context.session_id,
            "assistant",
            reply,
            structured_data=build_out_of_scope_structured_data(),
        )
        self._commit(chat_repo)
        return build_out_of_scope_response(security_context)

    def _out_of_scope_reply(self) -> str:
        return build_out_of_scope_reply()

    def _chat_security_context(
        self,
        request: ChatRequest,
        chat_repo: Any,
        principal: Principal | None,
        user_id: int | None,
    ) -> ChatSessionContext:
        if principal is None and user_id is not None:
            principal = Principal(subject=f"user:{user_id}", scopes=(), auth_type="user")
        if not hasattr(chat_repo, "get_session"):
            session = chat_repo.get_or_create_session(request.session_id, title=self._session_title(request))
            return ChatSessionContext(
                session_id=session.session_id or chat_repo.generate_session_id(),
                session_token=None,
                owner_subject=principal.subject if principal else None,
                owner_auth_type=principal.auth_type if principal else "anonymous",
                user_id=user_id,
            )
        return self.chat_session_security.get_or_create_context(
            chat_repo,
            session_id=request.session_id,
            title=self._session_title(request),
            principal=principal,
            session_token=request.session_token,
        )

    def generate_chat_stream(
        self,
        request: ChatRequest,
        db: Session,
        user_id: int | None = None,
        principal: Principal | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        from app.services.chat_stream_service import ChatStreamRunner

        return ChatStreamRunner(self).generate_events(request, db, user_id=user_id, principal=principal)

    def generate_guide_stream(
        self,
        request: ChatRequest,
        db: Session,
        user_id: int | None = None,
        principal: Principal | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        from app.services.chat_stream_service import ChatStreamRunner

        return ChatStreamRunner(self).generate_guide_events(request, db, user_id=user_id, principal=principal)

    def generate_follow_up_stream(
        self,
        request: ChatRequest,
        db: Session,
        user_id: int | None = None,
        principal: Principal | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        from app.services.chat_stream_service import ChatStreamRunner

        return ChatStreamRunner(self).generate_follow_up_events(request, db, user_id=user_id, principal=principal)

    async def _build_user_text(self, request: ChatRequest) -> str:
        text = request.message or ""
        if request.audio_url:
            self.media_url_policy.validate(request.audio_url)
            audio_text = await self.speech_service.extract_transcript(request.audio_url)
            text = self._join_text(text, audio_text)
        return text

    async def _build_image_info(self, request: ChatRequest) -> dict | None:
        if not request.image_url:
            return None
        self.media_url_policy.validate(request.image_url)
        return await self.vision_service.extract_image_info(request.image_url)

    def _load_history_context(self, chat_repo: Any, session_id: str) -> dict[str, Any]:
        prior_messages = chat_repo.list_messages(session_id)
        return self.chat_context_service.build_history_context(prior_messages)

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

    async def _handle_clarify(self, chat_repo: Any, security_context: ChatSessionContext, need: Any) -> ChatResponse:
        reply = await self.llm_client.generate_clarify_question(need)
        chat_repo.create_message(
            security_context.session_id,
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
            extra=build_security_extra(security_context),
        )

    async def _handle_recommendation(
        self,
        chat_repo: Any,
        security_context: ChatSessionContext,
        need: Any,
        db: Session,
        applied_preferences: AppliedPreferences,
    ) -> ChatResponse:
        session_id = security_context.session_id
        top_products, bundle_plans = await self._recommendation_results(need, db)
        reply, extra = await self._recommendation_reply(session_id, need, top_products, bundle_plans)
        extra.update(self._recommendation_extra(security_context))
        self._save_recommendation_result(
            chat_repo,
            security_context,
            reply,
            need,
            top_products,
            bundle_plans,
            applied_preferences,
            extra,
        )
        return build_recommendation_response(
            reply=reply,
            need=need,
            products=top_products,
            bundle_plans=bundle_plans,
            applied_preferences=applied_preferences,
            extra=extra,
        )

    def _recommendation_extra(self, security_context: ChatSessionContext) -> dict[str, Any]:
        extra = build_security_extra(security_context)
        extra.update(self._rag_fallback_meta())
        return extra

    def _save_recommendation_result(
        self,
        chat_repo: Any,
        security_context: ChatSessionContext,
        reply: str,
        need: Any,
        products: list[Any],
        bundle_plans: list[BundlePlan],
        applied_preferences: AppliedPreferences,
        extra: dict[str, Any],
    ) -> None:
        structured_data = build_assistant_structured_data(
            need=need,
            products=products,
            extra=extra,
            bundle_plans=bundle_plans,
            applied_preferences=applied_preferences,
        )
        chat_repo.create_message(security_context.session_id, "assistant", reply, structured_data=structured_data)
        chat_repo.create_recommendations(security_context.session_id, products)
        self._commit(chat_repo)

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
        return build_fallback_recommendation_reply(top_products), extra

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
        return build_chat_value_dump(value)

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
