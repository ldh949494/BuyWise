"""Chat visual-search helpers."""

from __future__ import annotations

from typing import Any, Callable

from sqlalchemy.orm import Session

from app.core.transaction import unit_of_work
from app.schemas.chat import ChatRequest, ChatResponse, StructuredNeed
from app.schemas.guide_preferences import AppliedPreferences
from app.schemas.visual_search import VisualSearchRequest
from app.services.visual_search_service import VisualSearchService


async def handle_visual_search_request(
    request: ChatRequest,
    text: str,
    chat_repo: Any,
    session_id: str,
    db: Session,
    visual_search_service: VisualSearchService,
    dump: Callable[[Any], Any] | None = None,
) -> ChatResponse:
    dump_value = dump or _dump
    result = await search_visual_products(request, text, db, visual_search_service)
    need = build_structured_need(result.recognized)
    reply = build_visual_search_reply(result.products, result.fallback_used)
    create_visual_search_message(chat_repo, session_id, reply, need, result, dump_value)
    _commit(chat_repo)
    return build_visual_search_response(session_id, reply, need, result)


async def search_visual_products(
    request: ChatRequest,
    text: str,
    db: Session,
    visual_search_service: VisualSearchService,
) -> Any:
    return await visual_search_service.search(
        VisualSearchRequest(image_url=request.image_url or "", message=text or None, top_k=8),
        db,
    )


def create_visual_search_message(
    chat_repo: Any,
    session_id: str,
    reply: str,
    need: StructuredNeed,
    result: Any,
    dump_value: Callable[[Any], Any],
) -> None:
    chat_repo.create_message(
        session_id,
        "assistant",
        reply,
        structured_data={
            "need": dump_value(need),
            "products": [dump_value(product) for product in result.products],
            "visual_search": result.model_dump(mode="json"),
        },
    )
    chat_repo.create_recommendations(session_id, result.products)


def build_visual_search_response(session_id: str, reply: str, need: StructuredNeed, result: Any) -> ChatResponse:
    return ChatResponse(
        reply=reply,
        need_clarify=False,
        structured_need=need,
        products=result.products,
        bundle_plans=[],
        applied_preferences=AppliedPreferences(),
        extra={"session_id": session_id, "visual_search": result.model_dump(mode="json")},
    )


def validate_visual_search_request(request: ChatRequest, text: str) -> bool:
    if not request.image_url:
        return False
    markers = ["同款", "类似", "相似", "找货", "找这件", "这件", "图里", "图片"]
    return not text.strip() or any(marker in text for marker in markers)


def build_visual_search_reply(products: list[Any], fallback_used: bool) -> str:
    if not products:
        return "我已识别图片特征，但当前商品池没有找到足够接近的候选。"
    names = "、".join(str(getattr(product, "name", "")) for product in products[:3] if getattr(product, "name", None))
    prefix = "我按图片特征和商品信息为你找到了相似候选"
    if fallback_used:
        prefix = "商品图索引暂未命中，我先按识图特征和文本检索为你找到了候选"
    return f"{prefix}：{names}。"


def build_structured_need(recognized: Any) -> StructuredNeed:
    preferences = [
        *getattr(recognized, "features", []),
        *getattr(recognized, "colors", []),
        *getattr(recognized, "materials", []),
    ]
    if getattr(recognized, "shape", None):
        preferences.append(recognized.shape)
    if getattr(recognized, "style", None):
        preferences.append(recognized.style)
    return StructuredNeed(
        intent="visual_search",
        category=getattr(recognized, "category", None),
        preferences=[str(item) for item in preferences if str(item).strip()],
        retrieval_strategy="strict",
        need_clarify=False,
    )


def _dump(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value


def _commit(chat_repo: Any) -> None:
    db = getattr(chat_repo, "db", None)
    if db is not None:
        with unit_of_work(db):
            pass
