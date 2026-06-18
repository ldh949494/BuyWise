"""LLM safety helpers for BuyWise guidance."""

from __future__ import annotations

from typing import Any

from app.core.metrics import count_agent_safety_block


UNSUPPORTED_CLAIM_KEYWORDS = [
    "优惠券",
    "券",
    "满减",
    "折扣",
    "打折",
    "促销",
    "包邮",
    "免邮",
    "保修",
    "售后",
    "官方认证",
    "正品保证",
    "闪购",
    "秒杀",
    "库存充足",
    "现货",
    "实时价格",
]


class AgentSafetyService:
    def guard_recommendation_reply(self, reply: str, products: list[Any], fallback: str) -> str:
        if not reply:
            count_agent_safety_block("output", "empty_reply")
            return fallback
        if self._has_unsupported_claim(reply, products):
            count_agent_safety_block("output", "unsupported_claim")
            return fallback
        if self._mentions_unknown_product(reply, products):
            count_agent_safety_block("output", "unknown_product")
            return fallback
        return reply

    def guard_follow_up_reply(self, reply: str, snapshot: dict[str, Any], fallback: str) -> str:
        products = snapshot.get("products") or []
        if not reply:
            count_agent_safety_block("follow_up_output", "empty_reply")
            return fallback
        if self._has_unsupported_claim(reply, products):
            count_agent_safety_block("follow_up_output", "unsupported_claim")
            return fallback
        return reply

    def _has_unsupported_claim(self, reply: str, products: list[Any]) -> bool:
        return any(keyword in reply and not self._claim_supported(keyword, products) for keyword in UNSUPPORTED_CLAIM_KEYWORDS)

    def _claim_supported(self, keyword: str, products: list[Any]) -> bool:
        return any(keyword in self._format_product(product) for product in products)

    def _mentions_unknown_product(self, reply: str, products: list[Any]) -> bool:
        names = [self._product_name(product) for product in products if self._product_name(product)]
        if not names:
            return False
        return "推荐" in reply and not any(name in reply for name in names)

    def _product_name(self, product: Any) -> str:
        if isinstance(product, dict):
            return str(product.get("name") or "")
        return str(getattr(product, "name", "") or "")

    def _format_product(self, product: Any) -> str:
        if isinstance(product, dict):
            return " ".join(str(value) for value in product.values())
        values = [getattr(product, key, "") for key in ("name", "reason", "tags", "platform", "stock_status")]
        return " ".join(str(value) for value in values)
