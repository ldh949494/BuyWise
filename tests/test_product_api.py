from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.config import settings
from app.main import create_app
from app.models import Product

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


def test_create_product_requires_authentication() -> None:
    settings.auth_api_keys = "tester:test-token:products:write"
    client = make_client()

    response = client.post(
        "/api/v1/products",
        json={"name": "Tablet", "category": "computer", "price": 2999.0},
    )

    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"
