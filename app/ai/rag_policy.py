"""RAG fallback, filtering, and reranking policies."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal
from typing import Any


DEFAULT_ADJACENT_CATEGORIES = {
    "学习用品": ["台灯", "机械键盘"],
    "机械键盘": ["台灯", "蓝牙耳机"],
    "蓝牙耳机": ["充电宝", "双肩包"],
    "台灯": ["机械键盘", "双肩包"],
    "充电宝": ["蓝牙耳机", "双肩包"],
    "双肩包": ["充电宝", "蓝牙耳机"],
}
DEFAULT_FALLBACK_BUDGET_MULTIPLIER = Decimal("1.15")
DEFAULT_FALLBACK_BUDGET_DELTA = Decimal("50")


class RagFallbackPolicy:
    def __init__(
        self,
        *,
        budget_multiplier: Decimal = DEFAULT_FALLBACK_BUDGET_MULTIPLIER,
        budget_delta: Decimal = DEFAULT_FALLBACK_BUDGET_DELTA,
        adjacent_categories: dict[str, list[str]] | None = None,
    ) -> None:
        self.budget_multiplier = budget_multiplier
        self.budget_delta = budget_delta
        self._adjacent_categories = adjacent_categories or DEFAULT_ADJACENT_CATEGORIES

    def list_stages(self) -> list[str]:
        return ["fallback_budget", "fallback_relaxed", "fallback_keyword", "fallback_adjacent", "fallback_popular"]

    def get_page_size(self, top_k: int) -> int:
        return max(top_k * 3, top_k)

    def get_relaxed_budget(self, budget_max: Any) -> Decimal | None:
        if budget_max is None:
            return None
        budget = Decimal(str(budget_max))
        return max(budget * self.budget_multiplier, budget + self.budget_delta)

    def list_adjacent_categories(self, category: str | None) -> list[str]:
        return self._adjacent_categories.get(category or "", [])


class RagFilterPolicy:
    def __init__(self, fallback_policy: RagFallbackPolicy | None = None) -> None:
        self.fallback_policy = fallback_policy or RagFallbackPolicy()

    def get_filtered_products(
        self,
        products: list[Any],
        need: Any,
        *,
        stage: str = "strict",
    ) -> tuple[list[Any], Counter[str]]:
        category = self._get_need_value(need, "category")
        budget_max = self._get_need_value(need, "budget_max")

        filtered = []
        reasons: Counter[str] = Counter()
        for product in products:
            if self._requires_exact_category(stage) and category and product.category != category:
                reasons["category_mismatch"] += 1
                continue
            if self._exceeds_budget(product, budget_max, stage=stage):
                reasons["over_budget"] += 1
                continue
            if product.stock is not None and product.stock <= 0:
                reasons["out_of_stock"] += 1
                continue
            filtered.append(product)
        return filtered, reasons

    def _exceeds_budget(self, product: Any, budget_max: Any, *, stage: str) -> bool:
        if budget_max is None or product.price is None:
            return False
        if stage in {"fallback_relaxed", "fallback_keyword", "fallback_adjacent", "fallback_popular"}:
            return False
        max_price = (
            self.fallback_policy.get_relaxed_budget(budget_max)
            if stage == "fallback_budget"
            else Decimal(str(budget_max))
        )
        return Decimal(str(product.price)) > max_price

    def _requires_exact_category(self, stage: str) -> bool:
        return stage in {"strict", "fallback_budget", "fallback_relaxed"}

    def _get_need_value(self, need: Any, key: str) -> Any:
        if isinstance(need, dict):
            return need.get(key)
        return getattr(need, key, None)


class RagRerankPolicy:
    def __init__(self, reranker: Any | None = None) -> None:
        self.reranker = reranker

    def rank_products(self, products: list[Any], need: Any) -> list[Any]:
        if self.reranker is None:
            return products
        products_by_id = {product.id: product for product in products}
        ranked_cards = self.reranker.rank(products, need)
        ranked_ids = [card.id for card in ranked_cards if card.id in products_by_id]
        return [products_by_id[product_id] for product_id in ranked_ids]
