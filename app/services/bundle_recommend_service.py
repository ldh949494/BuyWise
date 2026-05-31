"""Bundle recommendation assembly."""

from __future__ import annotations

from typing import Any

from app.services.recommend_service import RecommendService


class BundleRecommendService:
    def __init__(self, recommend_service: RecommendService | None = None) -> None:
        self.recommend_service = recommend_service or RecommendService()

    def rank(self, products: list[Any], need: Any) -> list[Any]:
        ranked_cards = self.recommend_service.rank(products, need)
        category_by_id = {product.id: getattr(product, "category", None) for product in products}
        return self._select_bundle_cards(ranked_cards, category_by_id, self._get_value(need, "budget_max"))

    def _select_bundle_cards(
        self,
        cards: list[Any],
        category_by_id: dict[int, str | None],
        budget_max: Any,
    ) -> list[Any]:
        selected = []
        selected_categories = set()
        total_price = 0.0
        for card in cards:
            category = category_by_id.get(card.id)
            if category in selected_categories:
                continue
            if budget_max is not None and selected and total_price + float(card.price) > float(budget_max):
                continue
            selected.append(card)
            if category:
                selected_categories.add(category)
            total_price += float(card.price)
            if len(selected) >= 5:
                break
        return selected or cards[:5]

    def _get_value(self, source: Any, key: str) -> Any:
        if isinstance(source, dict):
            return source.get(key)
        return getattr(source, key, None)
