from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Order, OrderItem, Review
from tests.test_admin_api import admin_headers, make_client_with_session_factory


def test_admin_ops_summary_exposes_beta_operations_audit(monkeypatch) -> None:
    client, session_factory = make_client_with_session_factory()
    headers = admin_headers(client)
    now = datetime.utcnow()
    settings.auth_api_keys = "smoke:smoke-token:orders:write,feedback:write;beta-alice:alice-token:orders:read"
    with session_factory() as db:
        seed_ops_audit_data(db, now)

    class FakeStore:
        def indexed_product_ids(self):
            return [1, 999]

        def count(self):
            return 2

    monkeypatch.setattr("app.services.admin_ops_service.ChromaProductStore", FakeStore)
    monkeypatch.setattr(
        "app.services.admin_ops_service.validate_readiness",
        lambda include_details=True: {
            "status": "not_ready",
            "service": "buywise-backend",
            "checks": {"database": {"status": "ok"}, "vector_index": {"status": "failed"}},
        },
    )

    response = client.get("/api/v1/admin/ops/summary", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["readiness"]["status"] == "not_ready"
    assert payload["index_health"]["status"] == "ok"
    assert payload["index_health"]["stale_product_ids"] == [999]
    assert payload["catalog"]["active_products"] == 1
    assert payload["operations"][0]["status"] == "manual"
    assert {token["subject"] for token in payload["token_guidance"]} == {"smoke", "beta-alice"}
    assert payload["recent_orders"][0]["external_platform"] == "jd"
    assert payload["pending_feedback"][0]["product_name"] == "Phone Pro"
    assert payload["recent_reviews"][0]["purchase_evidence"] == "buywise_recorded"


def seed_ops_audit_data(db: Session, now: datetime) -> None:
    order = Order(
        user_ref="smoke",
        payment_status="paid",
        fulfillment_status="delivered",
        external_platform="jd",
        external_order_ref="jd-1001",
        paid_at=now,
        delivered_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(order)
    db.flush()
    item = OrderItem(
        order_id=order.id,
        product_id=1,
        quantity=1,
        unit_price_snapshot=Decimal("1999.00"),
        name_snapshot="Phone Pro",
        platform_snapshot="jd",
        product_url_snapshot="https://example.test/phone",
        feedback_due_at=now - timedelta(hours=1),
        created_at=now,
    )
    db.add(item)
    db.flush()
    db.add(
        Review(
            product_id=1,
            order_item_id=item.id,
            user_ref="smoke",
            rating=Decimal("5.00"),
            content="closed beta smoke feedback",
            purchase_evidence="buywise_recorded",
            status="active",
            created_at=now,
        )
    )
    db.commit()
