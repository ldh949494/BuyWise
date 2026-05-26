from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.models.review import Review
from app.services.policies.review_weight_policy import ReviewWeightPolicy


FIXED_NOW = datetime(2026, 1, 15, 12, 0, 0)


def make_review(**kwargs) -> Review:
    defaults = {
        "product_id": 1,
        "rating": Decimal("5.0"),
        "sentiment": "positive",
        "content": "收货后体验稳定，符合预期",
        "submitted_at": FIXED_NOW - timedelta(days=7),
        "status": "active",
    }
    defaults.update(kwargs)
    return Review(**defaults)


def make_policy(**kwargs) -> ReviewWeightPolicy:
    defaults = {
        "imported_base_weight": 1.0,
        "verified_base_weight": 2.0,
        "weight_cap": 10.0,
    }
    defaults.update(kwargs)
    return ReviewWeightPolicy(**defaults)


def test_purchase_evidence_controls_base_weight() -> None:
    policy = make_policy()

    assert policy.get_weight(
        make_review(purchase_evidence=None, verified_purchase=False),
        now=FIXED_NOW,
    ) == pytest.approx(1.2)
    assert policy.get_weight(
        make_review(purchase_evidence="claimed", verified_purchase=False),
        now=FIXED_NOW,
    ) == pytest.approx(
        1.44
    )
    assert policy.get_weight(
        make_review(purchase_evidence="buywise_recorded", verified_purchase=False),
        now=FIXED_NOW,
    ) == pytest.approx(
        1.8
    )
    assert policy.get_weight(
        make_review(purchase_evidence="platform_verified", verified_purchase=True),
        now=FIXED_NOW,
    ) == pytest.approx(2.4)
    assert policy.get_weight(
        make_review(purchase_evidence=None, verified_purchase=True),
        now=FIXED_NOW,
    ) == pytest.approx(
        2.4,
    )


def test_timing_content_and_cap_shape_review_weight() -> None:
    policy = make_policy(weight_cap=2.0)

    assert policy.get_weight(
        make_review(submitted_at=FIXED_NOW - timedelta(days=1)),
        now=FIXED_NOW,
    ) == pytest.approx(0.8)
    assert policy.get_weight(make_review(submitted_at=FIXED_NOW - timedelta(days=90)), now=FIXED_NOW) == pytest.approx(
        1.0
    )
    assert policy.get_weight(
        make_review(submitted_at=FIXED_NOW - timedelta(days=365)),
        now=FIXED_NOW,
    ) == pytest.approx(
        0.7,
    )
    assert policy.get_weight(make_review(content="短评"), now=FIXED_NOW) == pytest.approx(0.84)
    assert policy.get_weight(make_review(pros_tags=["quiet"]), now=FIXED_NOW) == pytest.approx(1.32)
    assert policy.get_weight(
        make_review(purchase_evidence="platform_verified", verified_purchase=True, pros_tags=["quiet"]), now=FIXED_NOW
    ) == pytest.approx(2.0)
