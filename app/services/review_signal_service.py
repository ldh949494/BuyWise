"""Weighted review signal calculations."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal

from app.core.config import settings
from app.models.review import Review
from app.repositories.review_repo import ReviewRepository


class ReviewSignalService:
    def __init__(self, review_repo: ReviewRepository) -> None:
        self.review_repo = review_repo

    def get_metrics_for_products(self, product_ids: list[int]) -> dict[int, dict[str, object]]:
        reviews = self.review_repo.list_active_for_product_ids(product_ids)
        grouped: dict[int, list[Review]] = defaultdict(list)
        for review in reviews:
            if review.product_id is not None:
                grouped[int(review.product_id)].append(review)
        return {product_id: self._metrics(reviews) for product_id, reviews in grouped.items()}

    def get_weight(self, review: Review) -> float:
        base = self._base_weight(review)
        timing = self._timing_multiplier(review)
        content = self._content_multiplier(review)
        return min(base * timing * content, settings.review_weight_cap)

    def _base_weight(self, review: Review) -> float:
        evidence = (review.purchase_evidence or "").strip().lower()
        if evidence == "platform_verified":
            return settings.review_verified_base_weight
        if evidence == "buywise_recorded":
            return (settings.review_imported_base_weight + settings.review_verified_base_weight) / 2
        if evidence == "claimed":
            return settings.review_imported_base_weight * 1.2
        if review.verified_purchase:
            return settings.review_verified_base_weight
        return settings.review_imported_base_weight

    def _metrics(self, reviews: list[Review]) -> dict[str, object]:
        rating_total = 0.0
        rating_weight = 0.0
        sentiment_weight = {"positive": 0.0, "neutral": 0.0, "negative": 0.0}
        pro_tags: Counter[str] = Counter()
        con_tags: Counter[str] = Counter()
        expectation_known = 0
        expectation_met = 0
        verified_count = 0
        purchase_feedback_count = 0
        for review in reviews:
            weight = self.get_weight(review)
            if self._is_platform_verified(review):
                verified_count += 1
            if self._is_purchase_feedback(review):
                purchase_feedback_count += 1
            rating_total, rating_weight = self._add_rating(review, weight, rating_total, rating_weight)
            if review.sentiment in sentiment_weight:
                sentiment_weight[review.sentiment] += weight
            pro_tags.update(review.pros_tags or [])
            con_tags.update(review.cons_tags or [])
            expectation_known, expectation_met = self._add_expectation(review, expectation_known, expectation_met)
        return self._build_metrics_result(
            verified_count,
            rating_total,
            rating_weight,
            sentiment_weight,
            pro_tags,
            con_tags,
            expectation_known,
            expectation_met,
            purchase_feedback_count,
        )

    def _build_metrics_result(
        self,
        verified_count: int,
        rating_total: float,
        rating_weight: float,
        sentiment_weight: dict[str, float],
        pro_tags: Counter[str],
        con_tags: Counter[str],
        expectation_known: int,
        expectation_met: int,
        purchase_feedback_count: int,
    ) -> dict[str, object]:
        return {
            "verified_review_count": verified_count,
            "purchase_feedback_count": purchase_feedback_count,
            "weighted_rating": round(rating_total / rating_weight, 2) if rating_weight else None,
            "positive_weight": round(sentiment_weight["positive"], 2),
            "neutral_weight": round(sentiment_weight["neutral"], 2),
            "negative_weight": round(sentiment_weight["negative"], 2),
            "top_pro_tags": [tag for tag, _ in pro_tags.most_common(3)],
            "top_con_tags": [tag for tag, _ in con_tags.most_common(3)],
            "expectation_met_rate": round(expectation_met / expectation_known, 2) if expectation_known else None,
            "recent_feedback_count": purchase_feedback_count,
        }

    def _is_platform_verified(self, review: Review) -> bool:
        return (review.purchase_evidence or "").strip().lower() == "platform_verified" or bool(
            review.verified_purchase and not review.purchase_evidence
        )

    def _is_purchase_feedback(self, review: Review) -> bool:
        evidence = (review.purchase_evidence or "").strip().lower()
        return evidence in {"claimed", "buywise_recorded", "platform_verified"} or bool(review.verified_purchase)

    def _add_rating(self, review: Review, weight: float, total: float, rating_weight: float) -> tuple[float, float]:
        if review.rating is None:
            return total, rating_weight
        return total + float(Decimal(review.rating)) * weight, rating_weight + weight

    def _add_expectation(self, review: Review, known: int, met: int) -> tuple[int, int]:
        if review.met_expectation is None:
            return known, met
        return known + 1, met + int(review.met_expectation)

    def _timing_multiplier(self, review: Review) -> float:
        if not review.submitted_at:
            return 1.0
        age_days = (datetime.utcnow() - review.submitted_at).days
        if age_days <= 2:
            return 0.8
        if age_days <= 30:
            return 1.2
        if age_days <= 180:
            return 1.0
        return 0.7

    def _content_multiplier(self, review: Review) -> float:
        content = (review.content or "").strip()
        multiplier = 0.7 if len(content) < 10 else 1.0
        if review.pros_tags or review.cons_tags:
            multiplier *= 1.1
        return multiplier
