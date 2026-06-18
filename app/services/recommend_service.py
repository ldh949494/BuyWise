"""Recommendation service."""

from __future__ import annotations

from typing import Any

from app.schemas.chat import ProductCard
from app.services.policies.recommendation_scoring_policy import RecommendationScoringPolicy


class RecommendService:
    def __init__(self, scoring_policy: RecommendationScoringPolicy | None = None) -> None:
        self.scoring_policy = scoring_policy or RecommendationScoringPolicy()

    def rank(self, products: list[Any], need: Any) -> list[ProductCard]:
        cards = [self._rank_product(product, need) for product in products]
        cards = sorted(cards, key=lambda card: card.score or 0, reverse=True)
        self._attach_alternatives(cards)
        return cards

    def _rank_product(self, product: Any, need: Any) -> ProductCard:
        result = self.scoring_policy.build_score_result(product, need)

        return ProductCard(
            id=self._get_value(product, "id"),
            name=self._get_value(product, "name"),
            price=float(result.price) if result.price is not None else 0.0,
            category=self._get_value(product, "category"),
            platform=self._get_value(product, "platform"),
            product_url=self._get_value(product, "product_url"),
            stock_status=self._get_value(product, "stock_status"),
            image_url=self._get_value(product, "image_url"),
            rating=result.rating,
            score=result.score,
            tags=result.tags,
            reason="；".join(result.reasons) if result.reasons else None,
            budget_match=result.budget_match,
            scenario_match=result.scenario_match,
            conflicts=result.conflicts,
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
