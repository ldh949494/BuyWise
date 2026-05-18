"""Recommendation service."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any, List

from app.schemas.chat import ProductCard


class RecommendService:
    def rank(self, products: list[Any], need: Any) -> List[ProductCard]:
        cards = [self._rank_product(product, need) for product in products]
        cards = sorted(cards, key=lambda card: card.score or 0, reverse=True)
        self._attach_alternatives(cards)
        return cards

    def _rank_product(self, product: Any, need: Any) -> ProductCard:
        tags = self._coerce_list(self._get_value(product, "tags"))
        scenes = self._coerce_list(self._get_value(product, "suitable_scene"))
        preferences = self._coerce_list(self._get_value(need, "preferences"))
        avoid = self._coerce_list(self._get_value(need, "avoid"))

        score = 0.0
        reasons = []
        conflicts = []

        budget_match = None
        budget_max = self._get_value(need, "budget_max")
        price = self._get_value(product, "price")
        if budget_max is not None and price is not None:
            budget_match = Decimal(str(price)) <= Decimal(str(budget_max))
            if budget_match:
                score += 20
                reasons.append("价格符合预算")
            else:
                conflicts.append("超出预算")

        scenario_match = None
        scenario = self._get_value(need, "scenario")
        if scenario:
            scenario_match = scenario in scenes or any(scenario in scene for scene in scenes)
            if scenario_match:
                score += 15
                reasons.append(f"适合{scenario}场景")
            else:
                conflicts.append(f"{scenario}场景匹配不明确")

        preference_hits = 0
        searchable_values = tags + scenes + [str(self._get_value(product, "description") or "")]
        for preference in preferences:
            if preference_hits >= 3:
                break
            if self._contains_any(searchable_values, [preference]):
                score += 10
                preference_hits += 1
                reasons.append(f"符合{preference}偏好")

        for avoid_item in avoid:
            if self._contains_any(searchable_values, [avoid_item]):
                score -= 10
                conflicts.append(f"命中避雷项：{avoid_item}")

        rating = self._to_float(self._get_value(product, "rating"))
        if rating is not None:
            score += min(max(rating, 0), 5) / 5 * 15

        sales = self._to_float(self._get_value(product, "sales"))
        if sales is not None:
            score += min(max(sales, 0), 1000) / 1000 * 10

        stock = self._get_value(product, "stock")
        stock_status = self._get_value(product, "stock_status")
        if stock_status == "out_of_stock" or (stock is not None and stock <= 0):
            conflicts.append("库存不足")
            score -= 20
        elif stock is not None and stock > 0:
            score += 5
            reasons.append("库存充足")

        return ProductCard(
            id=self._get_value(product, "id"),
            name=self._get_value(product, "name"),
            price=float(price) if price is not None else 0.0,
            image_url=self._get_value(product, "image_url"),
            rating=rating,
            score=round(max(score, 0.0), 2),
            tags=tags,
            reason="；".join(reasons) if reasons else None,
            budget_match=budget_match,
            scenario_match=scenario_match,
            conflicts=conflicts,
        )

    def _attach_alternatives(self, cards: list[ProductCard]) -> None:
        for card in cards:
            if not card.conflicts:
                continue
            alternatives = [
                other.name
                for other in cards
                if other.id != card.id
                and len(other.conflicts) <= len(card.conflicts)
                and (other.price <= card.price or other.scenario_match is True)
            ]
            card.alternatives = alternatives[:3]

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

    def _contains_any(self, values: list[str], keywords: list[str]) -> bool:
        return any(keyword and keyword in value for value in values for keyword in keywords)

    def _try_parse_json(self, value: str) -> Any:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None

    def _to_float(self, value: Any) -> float | None:
        if value is None:
            return None
        return float(value)
