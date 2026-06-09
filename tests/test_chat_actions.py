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
        db.add(
            Product(
                name="Campus75 三模静音机械键盘",
                category="机械键盘",
                price=Decimal("299.00"),
                tags=["低噪音", "无线"],
                suitable_scene=["宿舍"],
                stock_status="in_stock",
            )
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


def test_chat_adds_latest_recommendation_to_cart_and_removes_by_position() -> None:
    client = make_client()
    session_id = "chat-action-session"

    recommend = client.post(
        "/api/v1/ai/chat",
        json={"session_id": session_id, "message": "推荐一个300以内适合宿舍的低噪音无线机械键盘"},
    )
    assert recommend.status_code == 200
    assert recommend.json()["products"][0]["id"] == 1

    add = client.post("/api/v1/ai/chat", json={"session_id": session_id, "message": "把刚才那款加到购物车"})
    assert add.status_code == 200
    assert add.json()["extra"]["action"] == "cart.add"
    assert "已加入购物车" in add.json()["reply"]
    assert client.get("/api/v1/cart").json()["items"][0]["product_id"] == 1

    remove = client.post("/api/v1/ai/chat", json={"session_id": session_id, "message": "删掉第一个"})
    assert remove.status_code == 200
    assert remove.json()["extra"]["action"] == "cart.remove"
    assert client.get("/api/v1/cart").json()["items"] == []


def test_chat_checkout_uses_default_address() -> None:
    client = make_client()
    session_id = "chat-checkout-session"
    client.post(
        "/api/v1/addresses",
        json={"receiver_name": "Alice", "phone": "13800138000", "detail": "默认地址", "is_default": True},
    )
    client.post("/api/v1/cart/items", json={"product_id": 1, "quantity": 1})

    checkout = client.post("/api/v1/ai/chat", json={"session_id": session_id, "message": "下单吧，地址用默认的"})

    assert checkout.status_code == 200
    assert checkout.json()["extra"]["action"] == "checkout.confirm"
    assert checkout.json()["extra"]["checkout"]["order"]["payment_mode"] == "shadow_paid"
    assert client.get("/api/v1/cart").json()["items"] == []
