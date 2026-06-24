"""Text assembly helpers."""

from __future__ import annotations

from decimal import Decimal
from typing import Any


def build_product_chunks(product: Any) -> list[dict[str, str]]:
    """Build field-scoped product chunks for embedding."""

    chunks = [
        _chunk("product_core", "core", _product_core_fields(product)),
        _chunk("specs", "specs", [("商品参数", _get_value(product, "specs"))]),
        _chunk("marketing_copy", "description", [("商品描述", _get_value(product, "description"))]),
        _chunk("review_summary", "review_summary", [("评论摘要", _get_value(product, "review_summary"))]),
    ]
    return [chunk for chunk in chunks if chunk["text"]]


def build_product_text(product: Any) -> str:
    """Build product text suitable for embedding."""

    lines = []
    for label, value in _product_fields(product):
        formatted = _format_value(value)
        if formatted:
            lines.append(f"{label}：{formatted}")
    return "\n".join(lines)


def _product_fields(product: Any) -> list[tuple[str, Any]]:
    return [
        ("商品名称", _get_value(product, "name")),
        ("类别", _get_value(product, "category")),
        ("品牌", _get_value(product, "brand")),
        ("SKU", _get_value(product, "sku")),
        ("平台", _get_value(product, "platform")),
        ("价格", _get_value(product, "price")),
        ("原价", _get_value(product, "original_price")),
        ("库存", _get_value(product, "stock")),
        ("库存状态", _get_value(product, "stock_status")),
        ("评分", _get_value(product, "rating")),
        ("销量", _get_value(product, "sales")),
        ("商品描述", _get_value(product, "description")),
        ("商品参数", _get_value(product, "specs")),
        ("商品标签", _get_value(product, "tags")),
        ("适合场景", _get_value(product, "suitable_scene")),
        ("评论摘要", _get_value(product, "review_summary")),
    ]


def _product_core_fields(product: Any) -> list[tuple[str, Any]]:
    return [
        ("商品名称", _get_value(product, "name")),
        ("类别", _get_value(product, "category")),
        ("品牌", _get_value(product, "brand")),
        ("SKU", _get_value(product, "sku")),
        ("平台", _get_value(product, "platform")),
        ("商品标签", _get_value(product, "tags")),
        ("适合场景", _get_value(product, "suitable_scene")),
    ]


def _chunk(chunk_type: str, field_path: str, fields: list[tuple[str, Any]]) -> dict[str, str]:
    lines = []
    for label, value in fields:
        formatted = _format_value(value)
        if formatted:
            lines.append(f"{label}：{formatted}")
    return {"chunk_type": chunk_type, "field_path": field_path, "text": "\n".join(lines)}


def build_query_from_need(need: Any) -> str:
    """Build a retrieval query from a structured shopping need."""

    fields = [
        ("意图", _get_value(need, "intent")),
        ("类别", _get_value(need, "category")),
        ("预算上限", _get_value(need, "budget_max")),
        ("场景", _get_value(need, "scenario")),
        ("偏好", _get_value(need, "preferences")),
        ("避免", _get_value(need, "avoid")),
        ("必选品类", _get_value(need, "must_have_categories")),
        ("排除品类", _get_value(need, "excluded_categories")),
    ]

    parts = []
    for label, value in fields:
        formatted = _format_value(value)
        if formatted:
            parts.append(f"{label}：{formatted}")
    return " ".join(parts)


def _get_value(source: Any, key: str) -> Any:
    if isinstance(source, dict):
        return source.get(key)
    return getattr(source, key, None)


def _format_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        return "；".join(
            f"{key}：{_format_scalar(item)}"
            for key, item in value.items()
            if _format_scalar(item)
        )
    if isinstance(value, (list, tuple, set)):
        return "、".join(
            formatted for item in value if (formatted := _format_scalar(item))
        )
    return _format_scalar(value)


def _format_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)
