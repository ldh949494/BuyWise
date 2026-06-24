"""Fast guide follow-up stream orchestration."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from typing import Any

from app.core.config import settings
from app.core.metrics import count_llm_failure
from app.core.traffic import is_capacity_limited
from app.ai.safety import AgentSafetyService
from app.schemas.chat import ChatRequest
from app.schemas.chat_stream import (
    ChatStreamDoneEventData,
    ChatStreamStatusEventData,
    ChatStreamTokenEventData,
)
from app.utils.guide_turn import build_turn_extra, list_string_values


class GuideFollowUpStreamService:
    def __init__(self, chat_service: Any, event_builder: Callable[[str, Any], dict[str, Any]]) -> None:
        self.chat_service = chat_service
        self._event = event_builder
        self.safety = AgentSafetyService()

    async def generate_events(
        self,
        context: dict[str, Any],
        request: ChatRequest,
        *,
        allow_recommendation: bool = False,
        recommendation_handler: Callable[[Any], AsyncIterator[dict[str, Any]]] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        yield self._event("status", ChatStreamStatusEventData(stage="context", message="follow_up_context"))
        text = (request.message or "").strip()
        if reason := self._missing_context_reason(request, text):
            async for event in self._stream_refresh_signal(context, reason):
                yield event
            return
        snapshot = self._latest_recommendation_snapshot(context)
        if snapshot is None:
            async for event in self._stream_refresh_signal(context, "missing_recommendation_snapshot"):
                yield event
            return
        self.chat_service._save_user_message(context["chat_repo"], context["session_id"], request, text, None)
        async for event in self._stream_follow_up_with_snapshot(
            context,
            text,
            snapshot,
            allow_recommendation=allow_recommendation,
            recommendation_handler=recommendation_handler,
        ):
            yield event

    async def _stream_follow_up_with_snapshot(
        self,
        context: dict[str, Any],
        text: str,
        snapshot: dict[str, Any],
        *,
        allow_recommendation: bool,
        recommendation_handler: Callable[[Any], AsyncIterator[dict[str, Any]]] | None,
    ) -> AsyncIterator[dict[str, Any]]:
        early_events = self._build_early_route(context, text, snapshot)
        if early_events is not None:
            async for event in early_events:
                yield event
            return
        decision = self._classify_turn(context, text)
        context["turn_type"] = decision.turn_type
        context["turn_reason"] = decision.reason
        if decision.get_should_recommend() and allow_recommendation and recommendation_handler is not None:
            async for event in recommendation_handler(decision.need):
                yield event
            return
        if decision.get_should_recommend() or self._should_refresh_follow_up(text, snapshot):
            async for event in self._stream_refresh_signal(context, "needs_new_recommendation"):
                yield event
            return
        context["turn_type"] = "answer_snapshot"
        context["turn_reason"] = decision.reason
        async for event in self._stream_follow_up_answer(context, text, snapshot):
            yield event

    def _build_early_route(
        self,
        context: dict[str, Any],
        text: str,
        snapshot: dict[str, Any],
    ) -> AsyncIterator[dict[str, Any]] | None:
        if action_result := self._execute_action_if_present(context, text):
            context["turn_type"] = "action"
            context["turn_reason"] = action_result.action
            return self._stream_action_result(context, action_result)
        if self._is_realtime_or_platform_claim_question(text):
            context["turn_type"] = "policy_limited"
            context["turn_reason"] = "platform_claim"
            return self._stream_policy_limited_answer(context, snapshot)
        return None

    def _classify_turn(self, context: dict[str, Any], text: str) -> Any:
        messages = context["chat_repo"].list_messages(context["session_id"], limit=20)
        state = self.chat_service.guide_state_builder.build(messages)
        history_context = self.chat_service.chat_context_service.build_history_context(messages)
        need = self.chat_service.intent_service.extract_by_rules(text, image_info=None, history_context=history_context)
        return self.chat_service.guide_turn_classifier.build_decision_for_need(text=text, need=need, state=state)

    def _missing_context_reason(self, request: ChatRequest, text: str) -> str | None:
        if not request.session_id or not text:
            return "missing_context"
        return None

    def _execute_action_if_present(self, context: dict[str, Any], text: str) -> Any:
        chat_repo = context["chat_repo"]
        db = chat_repo.db if hasattr(chat_repo, "db") else object()
        security_context = self._security_context(context)
        return self.chat_service._execute_chat_action(text, chat_repo, security_context, db)

    def _security_context(self, context: dict[str, Any]) -> Any:
        from app.services.chat_session_security import ChatSessionContext

        return ChatSessionContext(
            session_id=context["session_id"],
            session_token=context.get("session_token"),
            owner_subject=context.get("owner_subject"),
            owner_auth_type=context.get("owner_auth_type"),
            user_id=context.get("user_id"),
        )

    async def _stream_follow_up_answer(
        self,
        context: dict[str, Any],
        message: str,
        snapshot: dict[str, Any],
    ) -> AsyncIterator[dict[str, Any]]:
        context["stream_path"] = "follow_up_snapshot"
        yield self._event("status", ChatStreamStatusEventData(stage="generation", message="follow_up_generation"))
        chunks = []
        async for chunk in self._stream_follow_up_chunks(message, snapshot):
            if chunk["type"] == "status":
                yield self._event("status", ChatStreamStatusEventData(stage="fallback", message=chunk["message"]))
                continue
            chunks.append(chunk["text"])
            yield self._event("token", ChatStreamTokenEventData(text=chunk["text"]))
        reply = self._build_guarded_follow_up_reply(chunks, snapshot)
        if reply["degraded"]:
            self._save_follow_up_assistant(context, reply["text"], snapshot)
            yield self._event(
                "done",
                ChatStreamDoneEventData(
                    reply=reply["text"],
                    degraded=True,
                    degraded_reason=reply["degraded_reason"],
                    extra=build_turn_extra(context),
                ),
            )
            return
        self._save_follow_up_assistant(context, reply["text"], snapshot)
        yield self._event("done", ChatStreamDoneEventData(reply=reply["text"], extra=build_turn_extra(context)))

    async def _stream_follow_up_chunks(
        self,
        message: str,
        snapshot: dict[str, Any],
    ) -> AsyncIterator[dict[str, str]]:
        try:
            async for chunk in self.chat_service.llm_client.stream_chat(
                self._follow_up_messages(message, snapshot),
                max_tokens=settings.chat_stream_fast_reply_max_tokens,
            ):
                yield {"type": "token", "text": chunk}
        except Exception as exc:
            if not is_capacity_limited(exc, "llm"):
                raise
            count_llm_failure("follow_up", "capacity_limited")
            yield {"type": "status", "message": "llm_capacity_limited"}
            yield {"type": "token", "text": self._fallback_follow_up_reply(snapshot)}

    def _build_guarded_follow_up_reply(self, chunks: list[str], snapshot: dict[str, Any]) -> dict[str, Any]:
        fallback = self._fallback_follow_up_reply(snapshot)
        text = self.safety.guard_follow_up_reply("".join(chunks), snapshot, fallback)
        if self._looks_truncated(text):
            return {"text": fallback, "degraded": True, "degraded_reason": "follow_up_truncated"}
        return {"text": text, "degraded": False}

    async def _stream_policy_limited_answer(
        self,
        context: dict[str, Any],
        snapshot: dict[str, Any],
    ) -> AsyncIterator[dict[str, Any]]:
        context["stream_path"] = "follow_up_policy_limited"
        reply = self._policy_limited_reply(snapshot)
        self._save_follow_up_assistant(context, reply, snapshot)
        yield self._event("status", ChatStreamStatusEventData(stage="fallback", message="policy_limited"))
        yield self._event("token", ChatStreamTokenEventData(text=reply))
        yield self._event("done", ChatStreamDoneEventData(reply=reply, extra={"policy_limited": True, **build_turn_extra(context)}))

    async def _stream_action_result(self, context: dict[str, Any], action_result: Any) -> AsyncIterator[dict[str, Any]]:
        context["stream_path"] = "follow_up_action"
        structured_data = {"action": action_result.action, **action_result.data}
        context["chat_repo"].create_message(
            context["session_id"],
            "assistant",
            action_result.reply,
            structured_data=structured_data,
        )
        self.chat_service._commit(context["chat_repo"])
        yield self._event("status", ChatStreamStatusEventData(stage="action", message=action_result.action))
        yield self._event("token", ChatStreamTokenEventData(text=action_result.reply))
        yield self._event("done", ChatStreamDoneEventData(reply=action_result.reply, extra={**structured_data, **build_turn_extra(context)}))

    async def _stream_refresh_signal(
        self,
        context: dict[str, Any],
        reason: str,
    ) -> AsyncIterator[dict[str, Any]]:
        context["stream_path"] = "follow_up_refresh"
        reply = self._refresh_reply(reason)
        context["chat_repo"].create_message(
            context["session_id"],
            "assistant",
            reply,
            structured_data={"should_refresh": True, "refresh_reason": reason},
        )
        self.chat_service._commit(context["chat_repo"])
        yield self._event("status", ChatStreamStatusEventData(stage="refresh", message=reason))
        yield self._event(
            "done",
            ChatStreamDoneEventData(reply=reply, should_refresh=True, refresh_reason=reason, extra=build_turn_extra(context)),
        )

    def _save_follow_up_assistant(self, context: dict[str, Any], reply: str, snapshot: dict[str, Any]) -> None:
        context["chat_repo"].create_message(
            context["session_id"],
            "assistant",
            reply,
            structured_data={
                "follow_up": True,
                "need": snapshot.get("need"),
                "products": snapshot.get("products") or [],
                "bundle_plans": snapshot.get("bundle_plans") or [],
                "applied_preferences": snapshot.get("applied_preferences") or {},
                **build_turn_extra(context),
            },
        )
        self.chat_service._commit(context["chat_repo"])

    def _latest_recommendation_snapshot(self, context: dict[str, Any]) -> dict[str, Any] | None:
        for message in reversed(context["chat_repo"].list_messages(context["session_id"], limit=20)):
            structured_data = getattr(message, "structured_data", None) or {}
            products = structured_data.get("products") or []
            bundle_plans = structured_data.get("bundle_plans") or []
            if structured_data.get("need") and (products or bundle_plans):
                return structured_data
        return None

    def _should_refresh_follow_up(self, text: str, snapshot: dict[str, Any]) -> bool:
        normalized = text.strip().lower()
        refresh_markers = [
            "重新推荐",
            "重新生成推荐",
            "重新生成",
            "重新导购",
            "换一个",
            "换一批",
            "换品类",
            "换预算",
            "提高预算",
            "降低预算",
            "预算提高",
            "预算降低",
            "再推荐",
            "重新选",
            "不要这些",
            "改成",
        ]
        if any(marker in normalized for marker in refresh_markers):
            return True
        need = snapshot.get("need") or {}
        if self._has_structured_condition_change(text, need):
            return True
        category = str(need.get("category") or "").strip()
        recommendation_request_markers = ["推荐一个", "推荐一款", "推荐一下", "帮我推荐", "再推荐"]
        return bool(category and any(marker in normalized for marker in recommendation_request_markers) and category not in normalized)

    def _has_structured_condition_change(self, text: str, snapshot_need: dict[str, Any]) -> bool:
        if not snapshot_need:
            return False
        try:
            current_need = self.chat_service.intent_service.extract_by_rules(text, history_context=snapshot_need)
        except AttributeError:
            return False
        changed_fields = ["category", "budget_max", "scenario"]
        if any(self._field_changed(snapshot_need, current_need, field) for field in changed_fields):
            return True
        for field in ["preferences", "avoid", "style_preferences", "excluded_categories"]:
            if set(list_string_values(getattr(current_need, field, []))) != set(list_string_values(snapshot_need.get(field))):
                return True
        return False

    def _field_changed(self, snapshot_need: dict[str, Any], current_need: Any, field: str) -> bool:
        before = snapshot_need.get(field)
        after = getattr(current_need, field, None)
        return before not in (None, [], "") and after not in (None, [], "") and before != after

    def _is_realtime_or_platform_claim_question(self, text: str) -> bool:
        markers = [
            "优惠券",
            "包邮",
            "免邮",
            "满减",
            "折扣",
            "促销",
            "实时库存",
            "实时价格",
            "现货",
            "官方认证",
            "保修",
            "售后",
        ]
        return any(marker in text for marker in markers)

    def _looks_truncated(self, reply: str) -> bool:
        stripped = reply.strip()
        if not stripped:
            return False
        if stripped.endswith(("。", "！", "？", ".", "!", "?", "）", "】")):
            return False
        return len(stripped) >= max(settings.chat_stream_fast_reply_max_tokens - 20, 80)

    def _follow_up_messages(self, message: str, snapshot: dict[str, Any]) -> list[dict[str, str]]:
        return [
            {
                "role": "system",
                "content": (
                    "你是 BuyWise 的导购追问助手。只能基于已给出的导购快照回答，"
                    "不要新增未检索商品、不要编造优惠券、库存、实时价格或平台能力。"
                    "如果用户要求重新推荐、换预算或换品类，应简短说明需要刷新导购。"
                    "回答要简洁、可执行。"
                ),
            },
            {
                "role": "user",
                "content": f"已保存的导购快照：\n{self._snapshot_summary(snapshot)}\n\n用户追问：{message}",
            },
        ]

    def _snapshot_summary(self, snapshot: dict[str, Any]) -> str:
        need = snapshot.get("need") or {}
        products = snapshot.get("products") or []
        bundle_plans = snapshot.get("bundle_plans") or []
        lines = [f"需求：{need}"]
        if bundle_plans:
            lines.append(f"组合方案：{bundle_plans[:2]}")
        if products:
            product_lines = []
            for product in products[:5]:
                name = product.get("name") if isinstance(product, dict) else getattr(product, "name", "")
                price = product.get("price") if isinstance(product, dict) else getattr(product, "price", None)
                reason = product.get("reason") if isinstance(product, dict) else getattr(product, "reason", "")
                product_lines.append(f"- {name}，价格：{price}，理由：{reason}")
            lines.append("候选商品：\n" + "\n".join(product_lines))
        return "\n".join(lines)

    def _fallback_follow_up_reply(self, snapshot: dict[str, Any]) -> str:
        products = snapshot.get("products") or []
        if products:
            top = products[0]
            name = top.get("name") if isinstance(top, dict) else getattr(top, "name", "")
            reason = top.get("reason") if isinstance(top, dict) else getattr(top, "reason", "")
            return f"基于当前导购结果，优先看 {name}。主要理由是{reason or '它更贴近已记录的预算和偏好'}。"
        return "基于当前导购结果，可以继续围绕已给出的方案比较理由、风险和购买前注意。"

    def _policy_limited_reply(self, snapshot: dict[str, Any]) -> str:
        products = snapshot.get("products") or []
        if products:
            top = products[0]
            name = top.get("name") if isinstance(top, dict) else getattr(top, "name", "")
            return (
                "当前导购快照不能验证优惠券、包邮、实时库存、官方认证、保修或实时价格。"
                f"只能基于已保存的商品卡片继续比较；当前可优先参考 {name} 的价格、评分、标签和适用场景。"
            )
        return "当前导购快照不能验证优惠券、包邮、实时库存、官方认证、保修或实时价格；需要回到商品详情页或平台页面确认。"

    def _refresh_reply(self, reason: str) -> str:
        messages = {
            "missing_context": "需要先完成一次导购，再继续追问。",
            "missing_recommendation_snapshot": "当前没有可追问的导购结果，需要重新开始导购。",
            "needs_new_recommendation": "这个问题会改变推荐条件，需要刷新导购结果后再判断。",
        }
        return messages.get(reason, "需要刷新导购结果后再继续。")
