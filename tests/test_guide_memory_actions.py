from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import create_app
from app.models import Product


def make_client() -> TestClient:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with session_factory() as db:
        db.add_all(
            [
                Product(id=1, name="Campus75 三模静音机械键盘", category="机械键盘", price=Decimal("299.00"), tags=["低噪音", "无线"], suitable_scene=["宿舍"], stock_status="in_stock"),
                Product(id=2, name="Office68 轻薄无线机械键盘", category="机械键盘", price=Decimal("259.00"), tags=["无线"], suitable_scene=["办公"], stock_status="in_stock"),
                Product(id=3, name="DormLite 静音鼠标", category="鼠标", price=Decimal("89.00"), tags=["静音", "无线"], suitable_scene=["宿舍"], stock_status="in_stock"),
                Product(id=4, name="ProMouse 人体工学鼠标", category="鼠标", price=Decimal("159.00"), tags=["无线"], suitable_scene=["办公"], stock_status="in_stock"),
            ]
        )
        db.commit()

    app = create_app()

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_guide_stream_adds_featured_recommendation_to_cart() -> None:
    client = make_client()
    session_id = "guide-featured-cart"

    first = client.post("/api/v1/ai/guide/stream", json={"session_id": session_id, "message": "推荐两个300以内的无线机械键盘"})
    add = client.post("/api/v1/ai/guide/stream", json={"session_id": session_id, "message": "将你首推的商品添加到购物车中"})

    assert first.status_code == 200
    assert add.status_code == 200
    assert '"action":"cart.add"' in add.text
    assert client.get("/api/v1/cart").json()["items"][0]["product_id"] == 1


def test_guide_stream_open_ended_add_request_stays_non_mutating() -> None:
    client = make_client()
    session_id = "guide-open-ended-cart"

    client.post("/api/v1/ai/guide/stream", json={"session_id": session_id, "message": "推荐一个300以内的机械键盘"})
    response = client.post("/api/v1/ai/guide/stream", json={"session_id": session_id, "message": "帮我加购一副合适的键盘到购物车"})

    assert response.status_code == 200
    assert '"action":"cart.add"' not in response.text
    assert client.get("/api/v1/cart").json()["items"] == []


def test_pairing_mouse_recommendation_keeps_referenced_keyboard_in_bundle_plan() -> None:
    client = make_client()
    session_id = "guide-pairing-keyboard-mouse"

    first = client.post("/api/v1/ai/guide/stream", json={"session_id": session_id, "message": "推荐两个300以内的无线机械键盘"})
    second = client.post("/api/v1/ai/guide/stream", json={"session_id": session_id, "message": "推荐一款跟第一款键盘比较适配的鼠标"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert '"category":"鼠标"' in second.text
    assert "DormLite 静音鼠标" in second.text
    assert '"bundle_plans"' in second.text
    assert "Campus75 三模静音机械键盘" in second.text
    assert '"locked":true' in second.text


def test_pairing_pronoun_recommendation_keeps_keyboard_anchor_after_cart_action() -> None:
    client = make_client()
    session_id = "guide-pairing-pronoun-after-cart"

    client.post("/api/v1/ai/guide/stream", json={"session_id": session_id, "message": "推荐两个300以内的无线机械键盘"})
    client.post("/api/v1/ai/guide/stream", json={"session_id": session_id, "message": "将你首推的商品添加到购物车中"})
    response = client.post("/api/v1/ai/guide/stream", json={"session_id": session_id, "message": "再给我推荐一款跟它适配的鼠标"})

    assert response.status_code == 200
    assert '"should_refresh":true' not in response.text
    assert '"turn_type":"refresh_recommendation"' in response.text
    assert '"category":"鼠标"' in response.text
    assert "DormLite 静音鼠标" in response.text
    assert "Campus75 三模静音机械键盘" in response.text
    assert '"locked":true' in response.text


def test_incomplete_pairing_request_clarifies_target_category_without_refresh() -> None:
    client = make_client()
    session_id = "guide-pairing-missing-target"

    client.post("/api/v1/ai/guide/stream", json={"session_id": session_id, "message": "推荐两个300以内的无线机械键盘"})
    response = client.post("/api/v1/ai/guide/stream", json={"session_id": session_id, "message": "再给我推荐一款跟它"})

    assert response.status_code == 200
    assert '"should_refresh":true' not in response.text
    assert '"turn_type":"clarify"' in response.text
    assert '"turn_reason":"missing_pairing_category"' in response.text
    assert '"need_clarify":true' in response.text
    assert "推荐一款跟它适配的鼠标" in response.text


def test_later_reference_can_still_resolve_first_keyboard_after_mouse_turn() -> None:
    client = make_client()
    session_id = "guide-reference-previous-keyboard"

    client.post("/api/v1/ai/guide/stream", json={"session_id": session_id, "message": "推荐两个300以内的无线机械键盘"})
    client.post("/api/v1/ai/guide/stream", json={"session_id": session_id, "message": "推荐一款跟第一款键盘比较适配的鼠标"})
    add = client.post("/api/v1/ai/guide/stream", json={"session_id": session_id, "message": "把第一款键盘加到购物车"})

    assert add.status_code == 200
    assert '"action":"cart.add"' in add.text
    assert client.get("/api/v1/cart").json()["items"][0]["product_id"] == 1
