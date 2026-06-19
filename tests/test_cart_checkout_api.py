from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import create_app
from app.models import Product


def make_client() -> TestClient:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with testing_session_local() as db:
        db.add_all(
            [
                Product(
                    name="Quiet Keyboard",
                    category="机械键盘",
                    price=Decimal("299.00"),
                    platform="demo",
                    product_url="https://example.test/keyboard",
                    image_url="https://example.test/keyboard.jpg",
                    stock_status="in_stock",
                ),
                Product(
                    name="Travel Power Bank",
                    category="充电宝",
                    price=Decimal("139.00"),
                    platform="demo",
                    product_url="https://example.test/power",
                    stock_status="in_stock",
                ),
            ]
        )
        db.commit()

    app = create_app()

    def override_get_db():
        session = testing_session_local()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_cart_address_checkout_shadow_order_flow() -> None:
    client = make_client()

    address = client.post(
        "/api/v1/addresses",
        json={
            "receiver_name": "Alice",
            "phone": "13800138000",
            "province": "广东",
            "city": "深圳",
            "detail": "默认收货地址",
            "is_default": True,
        },
    )
    assert address.status_code == 201
    assert address.json()["is_default"] is True

    first = client.post("/api/v1/cart/items", json={"product_id": 1, "quantity": 1})
    second = client.post("/api/v1/cart/items", json={"product_id": 2, "quantity": 2})
    assert first.status_code == 201
    assert second.status_code == 201
    cart = second.json()
    assert cart["total_quantity"] == 3
    assert cart["total_price"] == 577.0

    update = client.patch(f"/api/v1/cart/items/{cart['items'][0]['id']}", json={"quantity": 2})
    assert update.status_code == 200
    assert update.json()["total_quantity"] == 4

    checkout = client.post("/api/v1/cart/checkout", json={"use_default_address": True})
    assert checkout.status_code == 201
    payload = checkout.json()
    assert payload["cart_cleared"] is True
    assert payload["order"]["payment_mode"] == "shadow_paid"
    assert payload["order"]["address_snapshot"]["receiver_name"] == "Alice"
    assert len(payload["order"]["items"]) == 2
    assert client.get("/api/v1/cart").json()["items"] == []


def test_cart_routes_are_registered() -> None:
    app = create_app()
    paths = set(app.openapi().get("paths", {}))

    assert "/api/v1/cart" in paths
    assert "/api/v1/cart/items" in paths
    assert "/api/v1/cart/checkout" in paths
    assert "/api/v1/addresses" in paths
