from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import create_app
from app.models import Product
from app.schemas.rag import RagSearchRequest
from app.services.rag_service import RagService


KEYBOARD_CATEGORY = "\u673a\u68b0\u952e\u76d8"
HEADPHONE_CATEGORY = "\u84dd\u7259\u8033\u673a"
KEYBOARD_NAME = "K87 \u9759\u97f3\u7ea2\u8f74\u673a\u68b0\u952e\u76d8"


def make_client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with session_factory() as db:
        db.add_all(
            [
                Product(
                    name=KEYBOARD_NAME,
                    category=KEYBOARD_CATEGORY,
                    price=Decimal("269.00"),
                    description="\u5bbf\u820d\u9759\u97f3\u5199\u4ee3\u7801",
                    tags=["\u9759\u97f3"],
                    stock=10,
                ),
                Product(
                    name="Gasket98 \u4e09\u6a21\u952e\u76d8",
                    category=KEYBOARD_CATEGORY,
                    price=Decimal("599.00"),
                    stock=10,
                ),
                Product(
                    name="AirBuds Lite",
                    category=HEADPHONE_CATEGORY,
                    price=Decimal("199.00"),
                    stock=10,
                ),
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


def test_rag_search_route_falls_back_to_product_table_filters() -> None:
    client = make_client()

    response = client.post(
        "/api/v1/rag/search",
        json={
            "query": "\u5bbf\u820d \u9759\u97f3 \u673a\u68b0\u952e\u76d8 300\u4ee5\u5185",
            "filters": {"category": KEYBOARD_CATEGORY, "price_max": 300},
            "top_k": 10,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "\u5bbf\u820d \u9759\u97f3 \u673a\u68b0\u952e\u76d8 300\u4ee5\u5185"
    assert payload["total"] == 1
    item = payload["items"][0]
    assert item["product_id"] == 1
    assert item["name"] == KEYBOARD_NAME
    assert item["price"] == 269.0
    assert item["score"] == 1.0
    assert item["reason"] == "\u6570\u636e\u5e93 fallback \u7ed3\u679c"
    assert "stock_status" in item


def test_rag_search_route_is_registered() -> None:
    app = create_app()
    paths = {route.path for route in app.routes}

    assert "/api/v1/rag/search" in paths


def test_rag_service_falls_back_when_vector_store_errors() -> None:
    client = make_client()
    db_override = next(iter(client.app.dependency_overrides.values()))
    db = next(db_override())

    class FailingStore:
        def search(self, query: str, top_k: int = 5):
            raise RuntimeError("dimension mismatch")

    response = RagService(product_store=FailingStore()).search(
        RagSearchRequest(
            query="\u5bbf\u820d \u9759\u97f3 \u673a\u68b0\u952e\u76d8 300\u4ee5\u5185",
            filters={"category": KEYBOARD_CATEGORY, "price_max": 300},
            top_k=10,
        ),
        db,
    )

    assert response.total == 1
    assert response.items[0].name == KEYBOARD_NAME
    assert response.items[0].reason == "\u6570\u636e\u5e93 fallback \u7ed3\u679c"


def test_rag_service_filters_stale_vector_product_ids() -> None:
    client = make_client()
    db_override = next(iter(client.app.dependency_overrides.values()))
    db = next(db_override())

    class FakeStore:
        def search(self, query: str, top_k: int = 5):
            return [
                {"id": "product_999", "metadata": {"product_id": 999, "name": "Stale"}, "score": 0.9},
                {
                    "id": "product_1",
                    "metadata": {
                        "product_id": 1,
                        "name": KEYBOARD_NAME,
                        "category": KEYBOARD_CATEGORY,
                        "price": 269,
                    },
                    "score": 0.8,
                },
            ]

    response = RagService(product_store=FakeStore()).search(
        RagSearchRequest(query="静音键盘", filters={"category": KEYBOARD_CATEGORY}, top_k=5),
        db,
    )

    assert [item.product_id for item in response.items] == [1]
