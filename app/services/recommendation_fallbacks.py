"""Fallback helpers for recommendation ranking and RAG metadata."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.schemas.chat import ProductCard


def rank_with_fallback(
    products: list[Any],
    need: Any,
    recommend_service: Any,
    *,
    get_value: Callable[[Any, str], Any],
    logger: Any,
) -> list[Any]:
    try:
        return recommend_service.rank(products, need)
    except (RuntimeError, TypeError, ValueError):
        logger.exception("Recommendation ranking failed; using deterministic fallback")
        return [_build_fallback_product_card(product, get_value) for product in _list_deterministic_product_order(products, get_value)]


def _list_deterministic_product_order(products: list[Any], get_value: Callable[[Any, str], Any]) -> list[Any]:
    return sorted(products, key=lambda product: _build_deterministic_product_key(product, get_value))


def _build_deterministic_product_key(product: Any, get_value: Callable[[Any, str], Any]) -> tuple[int, int, float, float, int]:
    stock = get_value(product, "stock")
    price = get_value(product, "price")
    rating = get_value(product, "rating")
    sales = get_value(product, "sales")
    has_stock = 1 if (stock is None or stock > 0) else 0
    has_price = 1 if price is not None else 0
    return (-has_stock, -has_price, -float(rating or 0), -float(sales or 0), int(get_value(product, "id") or 0))


def _build_fallback_product_card(product: Any, get_value: Callable[[Any, str], Any]) -> ProductCard:
    price = get_value(product, "price")
    rating = get_value(product, "rating")
    tags = get_value(product, "tags") or []
    if not isinstance(tags, list):
        tags = [str(tags)]
    return ProductCard(
        id=int(get_value(product, "id") or 0),
        name=str(get_value(product, "name") or "未命名商品"),
        price=float(price or 0),
        category=get_value(product, "category"),
        platform=get_value(product, "platform"),
        product_url=get_value(product, "product_url"),
        stock_status=get_value(product, "stock_status"),
        image_url=get_value(product, "image_url"),
        rating=float(rating) if rating is not None else None,
        score=0,
        tags=[str(tag) for tag in tags],
        reason="排序服务暂时不可用，先按库存、价格和口碑返回候选。",
    )


def build_rag_fallback_meta(rag_pipeline: Any) -> dict[str, Any]:
    diagnostics = getattr(rag_pipeline, "last_diagnostics", {}) or {}
    stage = diagnostics.get("fallback_stage")
    return {
        "fallback_used": bool(stage and stage not in {"strict", "none"}),
        "fallback_stage": stage,
        "result_quality": _get_result_quality(stage),
    }


def _get_result_quality(fallback_stage: Any) -> str:
    if fallback_stage in (None, "", "strict"):
        return "exact"
    if fallback_stage in {"fallback_budget", "fallback_relaxed"}:
        return "relaxed"
    if fallback_stage in {"fallback_keyword", "fallback_adjacent"}:
        return "broad"
    if fallback_stage in {"fallback_popular", "none"}:
        return "low_confidence"
    return "relaxed"
