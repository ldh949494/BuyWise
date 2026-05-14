"""Recommendation service."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any, List

from app.schemas.chat import ProductCard


class RecommendService:
    def rank(self, products: list[Any], need: Any) -> List[ProductCard]:
        cards = [self._rank_product(product, need) for product in products]
        return sorted(cards, key=lambda card: card.score or 0, reverse=True)

    def _rank_product(self, product: Any, need: Any) -> ProductCard:
        tags = self._coerce_list(self._get_value(product, "tags"))
        scenes = self._coerce_list(self._get_value(product, "suitable_scene"))
        preferences = self._coerce_list(self._get_value(need, "preferences"))

        score = 0.0
        reasons = []

        budget_max = self._get_value(need, "budget_max")
        price = self._get_value(product, "price")
        if budget_max is not None and price is not None:
            if Decimal(str(price)) <= Decimal(str(budget_max)):
                score += 20
                reasons.append("价格符合预算")

        scenario = self._get_value(need, "scenario")
        if scenario and scenario in scenes:
            score += 15
            reasons.append(f"适合{scenario}场景")

        preference_hits = 0
        for preference in preferences:
            if preference_hits >= 3:
                break
            if preference in tags:
                score += 10
                preference_hits += 1
                reasons.append(f"符合{preference}偏好")

        rating = self._to_float(self._get_value(product, "rating"))
        if rating is not None:
            score += min(max(rating, 0), 5) / 5 * 15

        sales = self._to_float(self._get_value(product, "sales"))
        if sales is not None:
            score += min(max(sales, 0), 1000) / 1000 * 10

        stock = self._get_value(product, "stock")
        if stock is not None and stock > 0:
            score += 5
            reasons.append("库存充足")

        return ProductCard(
            id=self._get_value(product, "id"),
            name=self._get_value(product, "name"),
            price=float(price) if price is not None else 0.0,
            image_url=self._get_value(product, "image_url"),
            rating=rating,
            score=round(score, 2),
            tags=tags,
            reason="；".join(reasons) if reasons else None,
        )

    def _get_value(self, source: Any, key: str) -> Any:
        if isinstance(source, dict):
            return source.get(key)
        return getattr(source, key, None)

    def _coerce_list(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            parsed = self._try_parse_json(value)
            if isinstance(parsed, list):
                return [str(item) for item in parsed if item]
            return [part.strip() for part in value.split(",") if part.strip()]
        if isinstance(value, list):
            return [str(item) for item in value if item]
        return [str(value)]

    def _try_parse_json(self, value: str) -> Any:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None

    def _to_float(self, value: Any) -> float | None:
        if value is None:
            return None
        return float(value)
