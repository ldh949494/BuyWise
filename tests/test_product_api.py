from decimal import Decimal

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.config import settings
from app.core.dependencies import get_product_service
from app.main import create_app
from app.models import Product
from app.schemas.product import ProductCreate
from app.services import product_service as product_service_module
from app.services.product_service import ProductService

AUTH_HEADER = {"Authorization": "Bearer test-token"}


def make_client():
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
            Product(name="Phone Pro", category="phone", price=Decimal("1999.00")),
            Product(name="Office Laptop", category="computer", price=Decimal("5999.00")),
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


def test_products_routes_are_registered() -> None:
    app = create_app()
    paths = {route.path for route in app.routes}

    assert "/api/v1/products" in paths
    assert "/api/v1/products/{product_id}" in paths


def test_list_products_returns_pydantic_response() -> None:
    client = make_client()

    response = client.get(
        "/api/v1/products",
        params={"category": "phone", "keyword": "Pro", "page": 1, "page_size": 20},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["name"] == "Phone Pro"


def test_get_product_returns_404_when_missing() -> None:
    client = make_client()

    response = client.get("/api/v1/products/999", headers={"X-Request-ID": "product-missing"})

    assert response.status_code == 404
    payload = response.json()
    assert response.headers["x-request-id"] == "product-missing"
    assert payload["detail"] == "Product not found"
    assert payload["code"] == "not_found"
    assert payload["extra"]["request_id"] == "product-missing"


def test_create_product_returns_created_product() -> None:
    settings.auth_api_keys = "tester:test-token:products:write"
    client = make_client()

    response = client.post(
        "/api/v1/products",
        json={"name": "Tablet", "category": "computer", "price": 2999.0},
        headers=AUTH_HEADER,
    )

    assert response.status_code == 201
    assert response.json()["id"] is not None
    assert response.json()["name"] == "Tablet"


def test_update_product_requires_auth_and_returns_updated_product() -> None:
    settings.auth_api_keys = "tester:test-token:products:write"
    client = make_client()

    response = client.patch(
        "/api/v1/products/1",
        json={"price": 1899.0, "tags": ["mobile", "deal"]},
        headers=AUTH_HEADER,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == 1
    assert payload["price"] == 1899.0
    assert payload["tags"] == ["mobile", "deal"]


def test_delete_product_soft_discontinues_and_filters_from_public_reads() -> None:
    settings.auth_api_keys = "tester:test-token:products:write"
    client = make_client()

    delete_response = client.delete("/api/v1/products/1", headers=AUTH_HEADER)
    list_response = client.get("/api/v1/products")
    detail_response = client.get("/api/v1/products/1")

    assert delete_response.status_code == 200
    assert delete_response.json()["stock_status"] == "discontinued"
    assert [item["id"] for item in list_response.json()["items"]] == [2]
    assert detail_response.status_code == 404


def test_create_product_requires_authentication() -> None:
    settings.auth_api_keys = "tester:test-token:products:write"
    client = make_client()

    response = client.post(
        "/api/v1/products",
        json={"name": "Tablet", "category": "computer", "price": 2999.0},
    )

    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"


def test_product_write_does_not_rollback_when_index_upsert_fails() -> None:
    settings.auth_api_keys = "tester:test-token:products:write"
    client = make_client()

    def failing_product_service(db=Depends(get_db)):
        def fail_index(product_ids):
            raise RuntimeError("index unavailable")

        return ProductService(db, index_updater=fail_index)

    client.app.dependency_overrides[get_product_service] = failing_product_service

    response = client.post(
        "/api/v1/products",
        json={"name": "Tablet", "category": "computer", "price": 2999.0},
        headers=AUTH_HEADER,
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Tablet"


def test_product_service_rolls_back_when_create_fails(monkeypatch) -> None:
    class FailingProductRepository:
        def __init__(self, db) -> None:
            self.db = db

        def create_product(self, product_data):
            raise RuntimeError("create failed")

    class FakeDb:
        def __init__(self) -> None:
            self.committed = False
            self.rolled_back = False

        def commit(self) -> None:
            self.committed = True

        def rollback(self) -> None:
            self.rolled_back = True

    monkeypatch.setattr(
        product_service_module,
        "ProductRepository",
        FailingProductRepository,
    )
    db = FakeDb()
    service = ProductService(db)

    with pytest.raises(RuntimeError):
        service.create_product(ProductCreate(name="Tablet"))

    assert db.committed is False
    assert db.rolled_back is True
