from datetime import date, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.compare import get_compare_service
from app.core.database import Base, get_db
from app.main import create_app
from app.models import PriceHistory, Product, Review
from app.services.compare_service import CompareService


KEYBOARD_CATEGORY = "\u673a\u68b0\u952e\u76d8"
KEYBOARD_NAME = "K87 \u9759\u97f3\u7ea2\u8f74\u673a\u68b0\u952e\u76d8"
USER_NEED = "\u5bbf\u820d\u4f7f\u7528\uff0c\u5b89\u9759\uff0c\u9884\u7b97300\u4ee5\u5185"


class FakeLLMClient:
    async def generate_compare_summary(self, user_need, products):
        return f"\u5982\u679c\u4f60\u6700\u5173\u6ce8\u5bbf\u820d\u9759\u97f3\uff0c\u4f18\u5148\u63a8\u8350 {products[0].name}\u3002"

    async def stream_chat(self, messages, **kwargs):
        yield "\u7ee7\u7eed\u5bf9\u6bd4\uff1a\u4f18\u5148\u770b\u9996\u63a8\u5546\u54c1\u3002"


class FailingLLMClient:
    async def generate_compare_summary(self, user_need, products):
        raise RuntimeError("llm unavailable")


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
    db.flush()
    db.add_all(
        [
            PriceHistory(product_id=products[0].id, date=date(2026, 5, 1), price=Decimal("299.00")),
            PriceHistory(product_id=products[0].id, date=date(2026, 5, 2), price=Decimal("289.00")),
            Review(
                product_id=products[0].id,
                user_ref="demo-user",
                user_name="buyer",
                rating=Decimal("5.0"),
                content="宿舍用很安静",
                sentiment="positive",
                source="buywise_post_delivery",
                verified_purchase=True,
                pros_tags=["quiet"],
                cons_tags=[],
                met_expectation=True,
                status="active",
                submitted_at=datetime(2026, 5, 1),
                created_at=datetime(2026, 5, 1),
            ),
        ]
    )
    db.commit()
    return [product.id for product in products]


@pytest.mark.anyio
async def test_compare_service_builds_items_with_rules_and_summary(monkeypatch) -> None:
    session_factory = make_session_factory()
    calls = []

    async def fake_threadpool(func, *args, **kwargs):
        calls.append(func.__name__)
        return func(*args, **kwargs)

    monkeypatch.setattr("app.services.compare_service.run_blocking_io", fake_threadpool)

    with session_factory() as db:
        product_ids = seed_products(db)
        service = CompareService(llm_client=FakeLLMClient())

        response = await service.compare(product_ids, USER_NEED, db)

    assert calls == ["_build_items"]
    assert response.summary == f"\u5982\u679c\u4f60\u6700\u5173\u6ce8\u5bbf\u820d\u9759\u97f3\uff0c\u4f18\u5148\u63a8\u8350 {KEYBOARD_NAME}\u3002"
    assert response.winner_id == product_ids[0]
    assert response.items[0].product_id == product_ids[0]
    assert response.items[0].name == KEYBOARD_NAME
    assert response.items[0].price == 269.0
    assert response.items[0].score > response.items[1].score
    assert "\u5b89\u9759" in response.items[0].pros
    assert "\u4ef7\u683c\u5408\u9002" in response.items[0].pros
    assert "\u9002\u5408\u5199\u4ee3\u7801" in response.items[0].pros
    assert "\u8fd1\u671f\u4ef7\u683c\u66f4\u4f4e" in response.items[0].pros
    assert "\u7528\u6237\u53cd\u9988\u8f83\u597d" in response.items[0].pros
    assert "已购反馈满意度高" in response.items[0].pros
    assert "\u4e0d\u652f\u6301\u65e0\u7ebf" in response.items[0].cons


@pytest.mark.anyio
async def test_compare_service_falls_back_when_llm_summary_fails(monkeypatch) -> None:
    session_factory = make_session_factory()

    async def fake_threadpool(func, *args, **kwargs):
        return func(*args, **kwargs)

    monkeypatch.setattr("app.services.compare_service.run_blocking_io", fake_threadpool)

    with session_factory() as db:
        product_ids = seed_products(db)
        service = CompareService(llm_client=FailingLLMClient())

        response = await service.compare(product_ids, USER_NEED, db)

    assert response.winner_id == product_ids[0]
    assert response.items
    assert response.summary is not None
    assert KEYBOARD_NAME in response.summary


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
    app.dependency_overrides[get_compare_service] = lambda: CompareService(
        llm_client=FakeLLMClient()
    )
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
    paths = set(app.openapi().get("paths", {}))

    assert "/api/v1/products/compare" in paths


def test_compare_follow_up_stream_does_not_require_guide_snapshot() -> None:
    app = create_app()
    app.dependency_overrides[get_compare_service] = lambda: CompareService(llm_client=FakeLLMClient())
    client = TestClient(app)

    response = client.post(
        "/api/v1/ai/compare/follow-up/stream",
        json={
            "message": "\u54ea\u4e2a\u66f4\u9002\u5408\u5bbf\u820d\uff1f",
            "summary": f"\u4f18\u5148\u63a8\u8350 {KEYBOARD_NAME}\u3002",
            "winner_id": 1,
            "items": [
                {
                    "id": 1,
                    "product_id": 1,
                    "name": KEYBOARD_NAME,
                    "price": 269.0,
                    "rating": 4.8,
                    "score": 90.0,
                    "pros": ["\u5b89\u9759", "\u4ef7\u683c\u5408\u9002"],
                    "cons": ["\u4e0d\u652f\u6301\u65e0\u7ebf"],
                },
                {
                    "id": 2,
                    "product_id": 2,
                    "name": "Lite68 \u529e\u516c\u9759\u97f3\u952e\u76d8",
                    "price": 329.0,
                    "rating": 4.5,
                    "score": 70.0,
                    "pros": ["\u65e0\u7ebf"],
                    "cons": ["\u8d85\u51fa\u9884\u7b97"],
                },
            ],
        },
    )

    assert response.status_code == 200
    assert "event: token" in response.text
    assert "event: done" in response.text
    assert "missing_recommendation_snapshot" not in response.text
