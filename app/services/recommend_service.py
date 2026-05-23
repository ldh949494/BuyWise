"""Recommendation service."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.schemas.chat import ProductCard
from app.utils.list_values import coerce_string_list

MAX_PREFERENCE_HITS = 3


class RecommendService:
    def rank(self, products: list[Any], need: Any) -> list[ProductCard]:
        cards = [self._rank_product(product, need) for product in products]
        cards = sorted(cards, key=lambda card: card.score or 0, reverse=True)
        self._attach_alternatives(cards)
        return cards

    def _rank_product(self, product: Any, need: Any) -> ProductCard:
        context = self._ranking_context(product, need)
        reasons = []
        conflicts = []
        budget_score, budget_match = self._score_budget(product, need, reasons, conflicts)
        scenario_score, scenario_match = self._score_scenario(need, context["scenes"], reasons)
        score = self._score_product(product, context, budget_score, scenario_score, reasons, conflicts)
        rating = self._to_float(self._get_value(product, "rating"))

        return ProductCard(
            id=self._get_value(product, "id"),
            name=self._get_value(product, "name"),
            price=float(context["price"]) if context["price"] is not None else 0.0,
            image_url=self._get_value(product, "image_url"),
            rating=rating,
            score=round(max(score, 0.0), 2),
            tags=context["tags"],
            reason="；".join(reasons) if reasons else None,
            budget_match=budget_match,
            scenario_match=scenario_match,
            conflicts=conflicts,
        )

    def _ranking_context(self, product: Any, need: Any) -> dict[str, Any]:
        tags = coerce_string_list(self._get_value(product, "tags"))
        scenes = coerce_string_list(self._get_value(product, "suitable_scene"))
        return {
            "tags": tags,
            "scenes": scenes,
            "preferences": coerce_string_list(self._get_value(need, "preferences")),
            "avoid": coerce_string_list(self._get_value(need, "avoid")),
            "price": self._get_value(product, "price"),
            "searchable_values": self._searchable_values(product, tags, scenes),
        }

    def _score_product(
        self,
        product: Any,
        context: dict[str, Any],
        budget_score: float,
        scenario_score: float,
        reasons: list[str],
        conflicts: list[str],
    ) -> float:
        return sum(
            [
                budget_score,
                scenario_score,
                self._score_preferences(context["preferences"], context["searchable_values"], reasons),
                self._score_avoid(context["avoid"], context["searchable_values"], conflicts),
                self._score_stock(product, reasons, conflicts),
                self._score_reputation(product),
                self._score_quality_signals(product, reasons, conflicts),
                self._score_verified_feedback(product, reasons, conflicts),
            ]
        )

    def _score_budget(
        self,
        product: Any,
        need: Any,
        reasons: list[str],
        conflicts: list[str],
    ) -> tuple[float, bool | None]:
        budget_max = self._get_value(need, "budget_max")
        price = self._get_value(product, "price")
        if budget_max is None or price is None:
            return 0.0, None
        budget_match = Decimal(str(price)) <= Decimal(str(budget_max))
        if budget_match:
            reasons.append("价格符合预算")
            return 20.0, True
        conflicts.append("超出预算")
        return -5.0, False

    def _score_scenario(
        self,
        need: Any,
        scenes: list[str],
        reasons: list[str],
    ) -> tuple[float, bool | None]:
        scenario = self._get_value(need, "scenario")
        if not scenario:
            return 0.0, None
        scenario_match = scenario in scenes or any(scenario in scene for scene in scenes)
        if not scenario_match:
            return 0.0, False
        reasons.append(f"适合{scenario}场景")
        return 15.0, True

    def _score_preferences(
        self,
        preferences: list[str],
        searchable_values: list[str],
        reasons: list[str],
    ) -> float:
        preference_hits = 0
        score = 0.0
        for preference in preferences:
            if preference_hits >= MAX_PREFERENCE_HITS:
                break
            if self._contains_any(searchable_values, [preference]):
                score += 10
                preference_hits += 1
                reasons.append(f"符合{preference}偏好")
        return score

    def _score_avoid(
        self,
        avoid: list[str],
        searchable_values: list[str],
        conflicts: list[str],
    ) -> float:
        score = 0.0
        for avoid_item in avoid:
            if self._contains_any(searchable_values, [avoid_item]):
                score -= 10
                conflicts.append(f"命中避雷项：{avoid_item}")
        return score

    def _score_stock(self, product: Any, reasons: list[str], conflicts: list[str]) -> float:
        stock = self._get_value(product, "stock")
        stock_status = self._get_value(product, "stock_status")
        if stock_status == "out_of_stock" or (stock is not None and stock <= 0):
            conflicts.append("库存不足")
            return -20.0
        if stock is not None and stock > 0:
            reasons.append("库存充足")
            return 5.0
        return 0.0

    def _score_reputation(self, product: Any) -> float:
        score = 0.0
        rating = self._to_float(self._get_value(product, "rating"))
        if rating is not None:
            score += min(max(rating, 0), 5) / 5 * 15
        sales = self._to_float(self._get_value(product, "sales"))
        if sales is not None:
            score += min(max(sales, 0), 1000) / 1000 * 10
        return score

    def _score_quality_signals(self, product: Any, reasons: list[str], conflicts: list[str]) -> float:
        score = 0.0
        price = self._get_value(product, "price")
        average_price = self._get_value(product, "price_history_average")
        if price is not None and average_price is not None:
            if Decimal(str(price)) < Decimal(str(average_price)):
                score += 4
                reasons.append("近期价格有优势")
            else:
                conflicts.append("价格优势不明显")

        sentiments = self._get_value(product, "review_sentiment_counts") or {}
        positive = int(sentiments.get("positive", 0) + sentiments.get("正向", 0))
        negative = int(sentiments.get("negative", 0) + sentiments.get("负向", 0))
        if positive > negative and positive > 0:
            score += 4
            reasons.append("用户反馈较好")
        elif negative > positive:
            score -= 4
            conflicts.append("存在负面反馈")
        return score

    def _score_verified_feedback(self, product: Any, reasons: list[str], conflicts: list[str]) -> float:
        metrics = self._get_value(product, "feedback_metrics") or {}
        weighted_rating = metrics.get("weighted_rating") if isinstance(metrics, dict) else None
        if not isinstance(weighted_rating, int | float):
            return 0.0
        if weighted_rating >= 4.2:
            reasons.append("已购反馈满意度高")
            return 6.0
        if weighted_rating <= 2.5:
            conflicts.append("已购反馈满意度偏低")
            return -6.0
        return 0.0

    def _searchable_values(self, product: Any, tags: list[str], scenes: list[str]) -> list[str]:
        values = tags + scenes
        for key in ["description", "review_summary"]:
            values.append(str(self._get_value(product, key) or ""))
        specs = self._get_value(product, "specs")
        if isinstance(specs, dict):
            values.extend(str(value) for value in specs.values() if value)
        elif specs:
            values.append(str(specs))
        return values

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

    def _contains_any(self, values: list[str], keywords: list[str]) -> bool:
        return any(keyword and keyword in value for value in values for keyword in keywords)

    def _to_float(self, value: Any) -> float | None:
        if value is None:
            return None
        return float(value)
