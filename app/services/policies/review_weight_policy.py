"""Review weight calculation policy."""

from __future__ import annotations

from datetime import datetime

from app.models.review import Review


class ReviewWeightPolicy:
    def __init__(
        self,
        *,
        imported_base_weight: float,
        verified_base_weight: float,
        weight_cap: float,
    ) -> None:
        self.imported_base_weight = imported_base_weight
        self.verified_base_weight = verified_base_weight
        self.weight_cap = weight_cap

    def get_weight(self, review: Review, *, now: datetime | None = None) -> float:
        base = self._base_weight(review)
        timing = self._timing_multiplier(review, now=now or datetime.utcnow())
        content = self._content_multiplier(review)
        return min(base * timing * content, self.weight_cap)

    def _base_weight(self, review: Review) -> float:
        evidence = (review.purchase_evidence or "").strip().lower()
        if evidence == "platform_verified":
            return self.verified_base_weight
        if evidence == "buywise_recorded":
            return (self.imported_base_weight + self.verified_base_weight) / 2
        if evidence == "claimed":
            return self.imported_base_weight * 1.2
        if review.verified_purchase:
            return self.verified_base_weight
        return self.imported_base_weight

    def _timing_multiplier(self, review: Review, *, now: datetime) -> float:
        if not review.submitted_at:
            return 1.0
        age_days = (now - review.submitted_at).days
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
