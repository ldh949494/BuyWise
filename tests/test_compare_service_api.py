from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import create_app
from app.models import Product
from app.services.compare_service import CompareService


KEYBOARD_CATEGORY = "\u673a\u68b0\u952e\u76d8"
KEYBOARD_NAME = "K87 \u9759\u97f3\u7ea2\u8f74\u673a\u68b0\u952e\u76d8"
USER_NEED = "\u5bbf\u820d\u4f7f\u7528\uff0c\u5b89\u9759\uff0c\u9884\u7b97300\u4ee5\u5185"


class FakeLLMClient:
    async def generate_compare_summary(self, user_need, products):
        return f"\u5982\u679c\u4f60\u6700\u5173\u6ce8\u5bbf\u820d\u9759\u97f3\uff0c\u4f18\u5148\u63a8\u8350 {products[0].name}\u3002"


def make_session_factory():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def seed_products(db):
    products = [
        Product(
            name=KEYBOARD_NAME,
            category=KEYBOARD_CATEGORY,
            price=Decimal("269.00"),
            rating=Decimal("4.8"),
            sales=1800,
            tags=["\u5b89\u9759", "\u9759\u97f3"],
            suitable_scene=["\u5bbf\u820d", "\u5199\u4ee3\u7801"],
            specs={"connection": "\u6709\u7ebf"},
            stock=10,
        ),
        Product(
            name="Lite68 \u529e\u516c\u9759\u97f3\u952e\u76d8",
            category=KEYBOARD_CATEGORY,
            price=Decimal("329.00"),
            rating=Decimal("4.5"),
            sales=600,
            tags=["\u9759\u97f3", "\u65e0\u7ebf"],
            suitable_scene=["\u529e\u516c"],
            specs={"connection": "\u65e0\u7ebf"},
            stock=8,
        ),
    ]
    db.add_all(products)
    db.commit()
    return [product.id for product in products]


@pytest.mark.anyio
async def test_compare_service_builds_items_with_rules_and_summary() -> None:
    session_factory = make_session_factory()
    with session_factory() as db:
        product_ids = seed_products(db)
        service = CompareService(llm_client=FakeLLMClient())

        response = await service.compare(product_ids, USER_NEED, db)

    assert response.summary == f"\u5982\u679c\u4f60\u6700\u5173\u6ce8\u5bbf\u820d\u9759\u97f3\uff0c\u4f18\u5148\u63a8\u8350 {KEYBOARD_NAME}\u3002"
    assert response.winner_id == product_ids[0]
    assert response.items[0].product_id == product_ids[0]
    assert response.items[0].name == KEYBOARD_NAME
    assert response.items[0].price == 269.0
    assert response.items[0].score > response.items[1].score
    assert "\u5b89\u9759" in response.items[0].pros
    assert "\u4ef7\u683c\u5408\u9002" in response.items[0].pros
    assert "\u9002\u5408\u5199\u4ee3\u7801" in response.items[0].pros
    assert "\u4e0d\u652f\u6301\u65e0\u7ebf" in response.items[0].cons


def test_compare_api_returns_frontend_ready_table_payload() -> None:
    session_factory = make_session_factory()
    with session_factory() as db:
        product_ids = seed_products(db)

    app = create_app()

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    response = client.post(
        "/api/v1/products/compare",
        json={"product_ids": product_ids, "user_need": USER_NEED},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["winner_id"] == product_ids[0]
    assert payload["items"][0]["product_id"] == product_ids[0]
    assert payload["items"][0]["name"] == KEYBOARD_NAME
    assert payload["items"][0]["pros"]
    assert payload["items"][0]["cons"]
    assert KEYBOARD_NAME in payload["summary"]


def test_compare_api_route_is_registered() -> None:
    app = create_app()
    paths = {route.path for route in app.routes}

    assert "/api/v1/products/compare" in paths
