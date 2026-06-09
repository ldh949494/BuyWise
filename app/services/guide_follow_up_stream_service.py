"""Fast guide follow-up stream orchestration."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from typing import Any

from app.core.config import settings
from app.core.metrics import count_llm_failure
from app.core.traffic import is_capacity_limited
from app.schemas.chat import ChatRequest
from app.schemas.chat_stream import (
    ChatStreamDoneEventData,
    ChatStreamStatusEventData,
    ChatStreamTokenEventData,
)


class GuideFollowUpStreamService:
    def __init__(self, chat_service: Any, event_builder: Callable[[str, Any], dict[str, Any]]) -> None:
        self.chat_service = chat_service
        self._event = event_builder

    async def generate_events(
        self,
        context: dict[str, Any],
        request: ChatRequest,
    ) -> AsyncIterator[dict[str, Any]]:
        yield self._event("status", ChatStreamStatusEventData(stage="context", message="follow_up_context"))
        text = (request.message or "").strip()
        if not request.session_id or not text:
            async for event in self._stream_refresh_signal(context, "missing_context"):
                yield event
            return
        snapshot = self._latest_recommendation_snapshot(context)
        if snapshot is None:
            async for event in self._stream_refresh_signal(context, "missing_recommendation_snapshot"):
                yield event
            return
        self.chat_service._save_user_message(context["chat_repo"], context["session_id"], request, text, None)
        if self._should_refresh_follow_up(text, snapshot):
            async for event in self._stream_refresh_signal(context, "needs_new_recommendation"):
                yield event
            return
        async for event in self._stream_follow_up_answer(context, text, snapshot):
            yield event

    async def _stream_follow_up_answer(
        self,
        context: dict[str, Any],
        message: str,
        snapshot: dict[str, Any],
    ) -> AsyncIterator[dict[str, Any]]:
        context["stream_path"] = "follow_up_snapshot"
        yield self._event("status", ChatStreamStatusEventData(stage="generation", message="follow_up_generation"))
        chunks = []
        try:
            async for chunk in self.chat_service.llm_client.stream_chat(
                self._follow_up_messages(message, snapshot),
                max_tokens=settings.chat_stream_fast_reply_max_tokens,
            ):
                chunks.append(chunk)
                yield self._event("token", ChatStreamTokenEventData(text=chunk))
        except Exception as exc:
            if not is_capacity_limited(exc, "llm"):
                raise
            count_llm_failure("follow_up", "capacity_limited")
            chunks = [self._fallback_follow_up_reply(snapshot)]
            yield self._event("status", ChatStreamStatusEventData(stage="fallback", message="llm_capacity_limited"))
            yield self._event("token", ChatStreamTokenEventData(text=chunks[0]))
        reply = "".join(chunks)
        self._save_follow_up_assistant(context, reply, snapshot)
        yield self._event("done", ChatStreamDoneEventData(reply=reply))

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
            ChatStreamDoneEventData(reply=reply, should_refresh=True, refresh_reason=reason),
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
            },
        )
        self.chat_service._commit(context["chat_repo"])

    def _latest_recommendation_snapshot(self, context: dict[str, Any]) -> dict[str, Any] | None:
        for message in context["chat_repo"].list_messages(context["session_id"], limit=20):
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
            "重新导购",
            "换一个",
            "换一批",
            "换品类",
            "换预算",
            "再推荐",
            "重新选",
            "不要这些",
            "改成",
        ]
        if any(marker in normalized for marker in refresh_markers):
            return True
        need = snapshot.get("need") or {}
        category = str(need.get("category") or "").strip()
        recommendation_request_markers = ["推荐一个", "推荐一款", "推荐一下", "帮我推荐", "再推荐"]
        return bool(category and any(marker in normalized for marker in recommendation_request_markers) and category not in normalized)

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

    def _refresh_reply(self, reason: str) -> str:
        messages = {
            "missing_context": "需要先完成一次导购，再继续追问。",
            "missing_recommendation_snapshot": "当前没有可追问的导购结果，需要重新开始导购。",
            "needs_new_recommendation": "这个问题会改变推荐条件，需要刷新导购结果后再判断。",
        }
        return messages.get(reason, "需要刷新导购结果后再继续。")
