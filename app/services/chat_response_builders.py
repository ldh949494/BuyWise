"""Chat response construction helpers."""

from __future__ import annotations

from typing import Any

from app.schemas.chat import BundlePlan, ChatResponse
from app.schemas.guide_preferences import AppliedPreferences
from app.services.chat_session_security import ChatSessionContext


def build_security_extra(security_context: ChatSessionContext) -> dict[str, Any]:
    extra: dict[str, Any] = {"session_id": security_context.session_id}
    if security_context.session_token:
        extra["session_token"] = security_context.session_token
    return extra


def build_recommendation_response(
    *,
    reply: str,
    need: Any,
    products: list[Any],
    bundle_plans: list[BundlePlan],
    applied_preferences: AppliedPreferences,
    extra: dict[str, Any],
) -> ChatResponse:
    return ChatResponse(
        reply=reply,
        need_clarify=False,
        structured_need=need,
        products=products,
        bundle_plans=bundle_plans,
        applied_preferences=applied_preferences,
        extra=extra,
    )
