from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.config import settings
from app.main import create_app
from app.models import Product
from app.services.user_token_service import build_user_access_token


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
                    name="Campus75 三模静音机械键盘",
                    category="机械键盘",
                    price=Decimal("299.00"),
                    tags=["低噪音", "无线"],
                    suitable_scene=["宿舍"],
                    stock_status="in_stock",
                ),
                Product(
                    name="DormLite 静音鼠标",
                    category="鼠标",
                    price=Decimal("89.00"),
                    tags=["静音", "无线"],
                    suitable_scene=["宿舍"],
                    stock_status="in_stock",
                ),
                Product(
                    name="Office68 轻薄无线机械键盘",
                    category="机械键盘",
                    price=Decimal("259.00"),
                    tags=["无线", "轻薄"],
                    suitable_scene=["办公"],
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


def test_chat_adds_second_recommended_product_with_quantity() -> None:
    client = make_client()
    session_id = "chat-action-second-product"

    recommend = client.post(
        "/api/v1/ai/chat",
        json={"session_id": session_id, "message": "推荐两个300以内的无线机械键盘"},
    )
    assert recommend.status_code == 200
    assert [product["id"] for product in recommend.json()["products"][:2]] == [1, 3]

    add = client.post(
        "/api/v1/ai/chat",
        json={"session_id": session_id, "message": "把第二款加到购物车，两件"},
    )

    assert add.status_code == 200
    assert add.json()["extra"]["action"] == "cart.add"
    assert add.json()["extra"]["product_ids"] == [3]
    cart_items = client.get("/api/v1/cart").json()["items"]
    assert len(cart_items) == 1
    assert cart_items[0]["product_id"] == 3
    assert cart_items[0]["quantity"] == 2


def test_chat_add_to_cart_requires_recommendation_context() -> None:
    client = make_client()

    add = client.post(
        "/api/v1/ai/chat",
        json={"session_id": "chat-action-no-context", "message": "把刚才那款加到购物车"},
    )

    assert add.status_code == 200
    assert add.json()["extra"]["action"] == "cart.add.needs_context"
    assert client.get("/api/v1/cart").json()["items"] == []


def test_chat_does_not_add_ambiguous_product_request_to_cart() -> None:
    client = make_client()
    session_id = "chat-action-ambiguous-add"

    recommend = client.post(
        "/api/v1/ai/chat",
        json={"session_id": session_id, "message": "推荐一个300以内适合宿舍的低噪音无线机械键盘"},
    )
    assert recommend.status_code == 200
    assert recommend.json()["products"]

    follow_up = client.post(
        "/api/v1/ai/chat",
        json={"session_id": session_id, "message": "帮我加购一副合适的键盘到购物车"},
    )

    assert follow_up.status_code == 200
    assert follow_up.json()["extra"].get("action") != "cart.add"
    assert follow_up.json()["products"]
    assert client.get("/api/v1/cart").json()["items"] == []


def test_chat_add_to_cart_requires_clear_reference_when_multiple_products_match() -> None:
    client = make_client()
    session_id = "chat-action-weak-reference"

    recommend = client.post(
        "/api/v1/ai/chat",
        json={"session_id": session_id, "message": "推荐两个300以内的无线机械键盘"},
    )
    assert recommend.status_code == 200
    assert len(recommend.json()["products"]) >= 2

    add = client.post("/api/v1/ai/chat", json={"session_id": session_id, "message": "把它加到购物车"})

    assert add.status_code == 200
    assert add.json()["extra"]["action"] == "cart.add.needs_reference"
    assert client.get("/api/v1/cart").json()["items"] == []


def test_chat_adds_bundle_plan_products_to_cart() -> None:
    client = make_client()
    session_id = "chat-action-bundle-plan"

    recommend = client.post(
        "/api/v1/ai/chat",
        json={"session_id": session_id, "message": "帮我搭配一套宿舍桌面外设方案，预算700以内"},
    )
    assert recommend.status_code == 200
    recommended_plan_ids = {
        item["product"]["id"]
        for item in recommend.json()["bundle_plans"][0]["items"]
    }
    assert recommended_plan_ids

    add = client.post(
        "/api/v1/ai/chat",
        json={"session_id": session_id, "message": "把这套方案加入购物车"},
    )

    assert add.status_code == 200
    assert add.json()["extra"]["action"] == "cart.add"
    assert set(add.json()["extra"]["product_ids"]) == recommended_plan_ids
    cart_items = client.get("/api/v1/cart").json()["items"]
    assert {item["product_id"] for item in cart_items} == recommended_plan_ids


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


def test_prod_chat_remove_confirmation_preserves_target_position() -> None:
    settings.app_env = "prod"
    settings.app_debug = False
    settings.auth_api_keys = "ops:ops-token:orders:read"
    settings.mysql_password = "secret"
    settings.readiness_token = "ready-token"
    settings.user_jwt_secret = "test-user-secret"
    settings.auth_otp_mock_enabled = False
    settings.allow_mock_providers_in_prod = True
    settings.chat_session_tokens_enabled = True
    settings.ai_media_url_allowlist_enabled = True
    client = make_client()
    access_token, _ = build_user_access_token(42)
    headers = {"Authorization": f"Bearer {access_token}"}

    client.post("/api/v1/cart/items", json={"product_id": 1, "quantity": 1}, headers=headers)
    client.post("/api/v1/cart/items", json={"product_id": 2, "quantity": 1}, headers=headers)

    pending = client.post(
        "/api/v1/ai/chat",
        json={"session_id": "prod-remove-confirm", "message": "删掉第二个"},
        headers=headers,
    )
    assert pending.status_code == 200
    assert pending.json()["extra"]["action_status"] == "pending_confirmation"
    assert [item["product_id"] for item in client.get("/api/v1/cart", headers=headers).json()["items"]] == [1, 2]

    ambiguous = client.post(
        "/api/v1/ai/chat",
        json={"session_id": "prod-remove-confirm", "message": "继续推荐"},
        headers=headers,
    )
    assert ambiguous.status_code == 200
    assert ambiguous.json()["extra"].get("action") != "cart.remove"
    assert [item["product_id"] for item in client.get("/api/v1/cart", headers=headers).json()["items"]] == [1, 2]

    confirmed = client.post(
        "/api/v1/ai/chat",
        json={"session_id": "prod-remove-confirm", "message": "确认"},
        headers=headers,
    )

    assert confirmed.status_code == 200
    assert confirmed.json()["extra"]["action"] == "cart.remove"
    assert confirmed.json()["extra"]["position"] == 2
    assert [item["product_id"] for item in client.get("/api/v1/cart", headers=headers).json()["items"]] == [1]
