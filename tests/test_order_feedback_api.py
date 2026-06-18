from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import create_app
from app.models import Product


def configure_valid_prod_settings(auth_api_keys: str) -> None:
    settings.app_env = "prod"
    settings.app_debug = False
    settings.mysql_password = "secret"
    settings.readiness_token = "ready-token"
    settings.user_jwt_secret = "user-jwt-secret"
    settings.auth_otp_mock_enabled = False
    settings.allow_mock_providers_in_prod = True
    settings.chat_session_tokens_enabled = True
    settings.ai_media_url_allowlist_enabled = True
    settings.auth_api_keys = auth_api_keys


def make_client() -> TestClient:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = testing_session_local()
    db.add_all(
        [
            Product(
                name="Quiet Keyboard",
                category="keyboard",
                price=Decimal("299.00"),
                platform="demo",
                product_url="https://example.test/keyboard",
                stock_status="in_stock",
            ),
            Product(name="Sold Out Mouse", category="mouse", price=Decimal("99.00"), stock_status="out_of_stock"),
        ]
    )
    db.commit()
    db.close()

    app = create_app()

    def override_get_db():
        session = testing_session_local()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_order_feedback_routes_are_registered() -> None:
    app = create_app()
    paths = {route.path for route in app.routes}

    assert "/api/v1/orders" in paths
    assert "/api/v1/orders/{order_id}/advance" in paths
    assert "/api/v1/feedback/prompts" in paths
    assert "/api/v1/reviews/from-order-item" in paths


def test_simulated_order_feedback_loop() -> None:
    settings.feedback_delay_days = 0
    client = make_client()

    create_response = client.post("/api/v1/orders", json={"product_id": 1, "quantity": 1})
    assert create_response.status_code == 201
    order = create_response.json()
    assert order["payment_status"] == "paid"
    assert order["fulfillment_status"] == "pending"
    assert order["items"][0]["name_snapshot"] == "Quiet Keyboard"

    shipped_response = client.post(f"/api/v1/orders/{order['id']}/advance")
    delivered_response = client.post(f"/api/v1/orders/{order['id']}/advance")
    assert shipped_response.json()["fulfillment_status"] == "shipped"
    delivered = delivered_response.json()
    assert delivered["fulfillment_status"] == "delivered"
    order_item_id = delivered["items"][0]["id"]
    assert delivered["items"][0]["feedback_due_at"] is not None

    prompts_response = client.get("/api/v1/feedback/prompts")
    assert prompts_response.status_code == 200
    prompts = prompts_response.json()["items"]
    assert prompts[0]["order_item_id"] == order_item_id
    assert prompts[0]["product_name"] == "Quiet Keyboard"

    review_response = client.post(
        "/api/v1/reviews/from-order-item",
        json={
            "order_item_id": order_item_id,
            "rating": 5,
            "content": "用了几天很安静，办公和宿舍都合适",
            "usage_context": "office",
            "pros_tags": ["quiet", "good_value"],
            "cons_tags": [],
            "met_expectation": True,
        },
    )
    assert review_response.status_code == 201
    review = review_response.json()
    assert review["verified_purchase"] is False
    assert review["purchase_evidence"] == "buywise_recorded"
    assert review["source"] == "buywise_post_delivery"
    assert review["sentiment"] == "positive"

    duplicate_response = client.post(
        "/api/v1/reviews/from-order-item",
        json={"order_item_id": order_item_id, "rating": 4, "content": "重复评价应该失败"},
    )
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["code"] == "duplicate_feedback"

    assert client.get("/api/v1/feedback/prompts").json()["items"] == []

    update_response = client.put(
        f"/api/v1/reviews/{review['id']}",
        json={"rating": 2, "content": "后来发现按键有杂音", "cons_tags": ["noisy"], "met_expectation": False},
    )
    assert update_response.status_code == 200
    assert update_response.json()["sentiment"] == "negative"

    withdraw_response = client.post(f"/api/v1/reviews/{review['id']}/withdraw")
    assert withdraw_response.status_code == 200
    assert withdraw_response.json()["status"] == "withdrawn"


def test_order_rejects_out_of_stock_product() -> None:
    client = make_client()

    response = client.post("/api/v1/orders", json={"product_id": 2})

    assert response.status_code == 409
    assert response.json()["code"] == "out_of_stock"


def test_review_requires_delivered_order_item() -> None:
    client = make_client()
    order = client.post("/api/v1/orders", json={"product_id": 1}).json()
    order_item_id = order["items"][0]["id"]

    response = client.post(
        "/api/v1/reviews/from-order-item",
        json={"order_item_id": order_item_id, "rating": 5, "content": "还没收货不能评价"},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "not_delivered"


def test_prod_order_feedback_requires_bearer_token() -> None:
    configure_valid_prod_settings("beta:beta-token:orders:read,orders:write,feedback:read,feedback:write")
    client = make_client()

    response = client.post("/api/v1/orders", json={"product_id": 1})

    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"


def test_prod_order_feedback_rejects_missing_scope() -> None:
    configure_valid_prod_settings("beta:beta-token:orders:read")
    client = make_client()

    response = client.post(
        "/api/v1/orders",
        json={"product_id": 1},
        headers={"Authorization": "Bearer beta-token"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


def test_prod_order_feedback_uses_token_subject_for_user_ref() -> None:
    settings.external_purchase_feedback_mode = "immediate"
    settings.feedback_delay_days = 0
    configure_valid_prod_settings(
        "alice:alice-token:orders:read,orders:write,feedback:read,feedback:write;"
        "bob:bob-token:orders:read,orders:write,feedback:read,feedback:write"
    )
    client = make_client()
    alice_headers = {"Authorization": "Bearer alice-token"}
    bob_headers = {"Authorization": "Bearer bob-token"}

    order_response = client.post(
        "/api/v1/orders",
        json={"product_id": 1, "external_platform": "tmall"},
        headers=alice_headers,
    )
    order = order_response.json()

    alice_prompts = client.get("/api/v1/feedback/prompts", headers=alice_headers).json()["items"]
    bob_prompts = client.get("/api/v1/feedback/prompts", headers=bob_headers).json()["items"]

    assert order_response.status_code == 201
    assert order["user_ref"] == "alice"
    assert order["fulfillment_status"] == "delivered"
    assert alice_prompts
    assert bob_prompts == []


def test_prod_order_advance_requires_advance_scope() -> None:
    configure_valid_prod_settings(
        "beta:beta-token:orders:read,orders:write,feedback:read,feedback:write;"
        "beta:advance-token:orders:read,orders:write,orders:advance"
    )
    client = make_client()
    order = client.post(
        "/api/v1/orders",
        json={"product_id": 1},
        headers={"Authorization": "Bearer beta-token"},
    ).json()

    denied = client.post(f"/api/v1/orders/{order['id']}/advance", headers={"Authorization": "Bearer beta-token"})
    allowed = client.post(f"/api/v1/orders/{order['id']}/advance", headers={"Authorization": "Bearer advance-token"})

    assert denied.status_code == 403
    assert allowed.status_code == 200
    assert allowed.json()["fulfillment_status"] == "shipped"
