"""Chat response construction helpers."""

from __future__ import annotations

from typing import Any

from app.schemas.chat import BundlePlan, ChatResponse
from app.schemas.guide_preferences import AppliedPreferences
from app.services.chat_session_security import ChatSessionContext
from app.utils.taxonomy import OUT_OF_SCOPE_INTENT


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


def build_assistant_structured_data(
    *,
    need: Any,
    products: list[Any],
    extra: dict[str, Any],
    bundle_plans: list[BundlePlan] | None = None,
    applied_preferences: AppliedPreferences | None = None,
) -> dict[str, Any]:
    structured_data = {
        "need": build_chat_value_dump(need),
        "products": [build_chat_value_dump(product) for product in products],
        "applied_preferences": build_chat_value_dump(applied_preferences or AppliedPreferences()),
    }
    if bundle_plans:
        structured_data["bundle_plans"] = [build_chat_value_dump(plan) for plan in bundle_plans]
    for key in ["fallback_used", "fallback_stage", "result_quality"]:
        if key in extra:
            structured_data[key] = extra[key]
    if extra.get("degraded"):
        structured_data["degraded"] = True
        structured_data["degraded_reason"] = extra["degraded_reason"]
    return structured_data


def build_fallback_recommendation_reply(products: list[Any]) -> str:
    if not products:
        return "没有找到匹配商品。可以换个品类、商品名，或放宽预算和偏好后再试。"
    names = "、".join(str(getattr(product, "name", "")) for product in products[:3] if getattr(product, "name", None))
    if names:
        return f"当前 AI 总结暂时繁忙，先为你返回基础推荐：{names}。你可以先查看商品卡片。"
    return "当前 AI 总结暂时繁忙，先为你返回基础推荐。你可以先查看商品卡片。"


def build_chat_value_dump(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value


def validate_out_of_scope_need(need: Any, get_value: Any) -> bool:
    return get_value(need, "intent") == OUT_OF_SCOPE_INTENT


def build_out_of_scope_reply() -> str:
    return "我只能帮助你在 BuyWise 商品库里做导购、对比和购买前决策；这个请求超出了导购助手范围。你可以告诉我想买的品类、预算和使用场景，我再继续推荐。"


def build_out_of_scope_response(security_context: ChatSessionContext) -> ChatResponse:
    return ChatResponse(
        reply=build_out_of_scope_reply(),
        need_clarify=False,
        structured_need=None,
        products=[],
        bundle_plans=[],
        applied_preferences=AppliedPreferences(),
        extra={**build_security_extra(security_context), "out_of_scope": True},
    )


def build_out_of_scope_structured_data() -> dict[str, Any]:
    return {"need": {"intent": OUT_OF_SCOPE_INTENT}, "need_clarify": False, "out_of_scope": True}
