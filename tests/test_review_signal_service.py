from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.core.config import settings
from app.models.review import Review
from app.services.review_signal_service import ReviewSignalService


class FakeReviewRepository:
    def __init__(self, reviews: list[Review]) -> None:
        self.reviews = reviews

    def list_active_for_product_ids(self, product_ids: list[int]) -> list[Review]:
        return [review for review in self.reviews if review.product_id in product_ids]


def make_review(**kwargs) -> Review:
    defaults = {
        "product_id": 1,
        "rating": Decimal("5.0"),
        "sentiment": "positive",
        "content": "收货后体验稳定，符合预期",
        "submitted_at": datetime.utcnow() - timedelta(days=7),
        "status": "active",
    }
    defaults.update(kwargs)
    return Review(**defaults)


def test_purchase_evidence_controls_review_weight_and_counts() -> None:
    settings.review_imported_base_weight = 1.0
    settings.review_verified_base_weight = 2.0
    settings.review_weight_cap = 10.0
    service = ReviewSignalService(
        FakeReviewRepository(
            [
                make_review(purchase_evidence=None, verified_purchase=False),
                make_review(purchase_evidence="claimed", verified_purchase=False),
                make_review(purchase_evidence="buywise_recorded", verified_purchase=False),
                make_review(purchase_evidence="platform_verified", verified_purchase=True),
            ]
        )
    )

    metrics = service.get_metrics_for_products([1])[1]

    assert service.get_weight(make_review(purchase_evidence=None, verified_purchase=False)) == pytest.approx(1.2)
    assert service.get_weight(make_review(purchase_evidence="claimed", verified_purchase=False)) == pytest.approx(1.44)
    assert service.get_weight(make_review(purchase_evidence="buywise_recorded", verified_purchase=False)) == pytest.approx(1.8)
    assert service.get_weight(make_review(purchase_evidence="platform_verified", verified_purchase=True)) == pytest.approx(2.4)
    assert metrics["verified_review_count"] == 1
    assert metrics["purchase_feedback_count"] == 3
    assert metrics["recent_feedback_count"] == 3
