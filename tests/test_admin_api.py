from decimal import Decimal
from io import BytesIO

from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.dependencies import get_product_service
from app.main import create_app
from app.models import AdminUser, Product
from app.services.admin_auth_service import build_password_hash
from app.services.product_service import ProductService


ADMIN_PASSWORD = "correct horse battery"


def make_client():
    settings.admin_jwt_secret = "test-admin-secret"
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = testing_session_local()
    db.add(AdminUser(username="admin", password_hash=build_password_hash(ADMIN_PASSWORD), role="admin"))
    db.add(Product(name="Phone Pro", category="phone", price=Decimal("1999.00")))
    db.commit()
    db.close()

    app = create_app()

    def override_get_db():
        session = testing_session_local()
        try:
            yield session
        finally:
            session.close()

    def override_product_service(db=Depends(get_db)):
        return ProductService(db, index_updater=None)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_product_service] = override_product_service
    return TestClient(app)


def admin_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/admin/auth/login",
        json={"username": "admin", "password": ADMIN_PASSWORD},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_admin_routes_are_registered() -> None:
    app = create_app()
    paths = {route.path for route in app.routes}

    assert "/api/v1/admin/auth/login" in paths
    assert "/api/v1/admin/products" in paths
    assert "/api/v1/admin/upload" in paths


def test_admin_login_returns_access_token() -> None:
    client = make_client()

    response = client.post(
        "/api/v1/admin/auth/login",
        json={"username": "admin", "password": ADMIN_PASSWORD},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["expires_in"] == 480 * 60
    assert payload["access_token"].count(".") == 2


def test_admin_login_rejects_invalid_password_with_generic_error() -> None:
    client = make_client()

    response = client.post(
        "/api/v1/admin/auth/login",
        json={"username": "admin", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password."


def test_admin_products_require_jwt() -> None:
    client = make_client()

    response = client.get("/api/v1/admin/products")

    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"


def test_admin_can_create_update_and_delete_product() -> None:
    client = make_client()
    headers = admin_headers(client)

    create_response = client.post(
        "/api/v1/admin/products",
        json={"name": "Tablet", "category": "computer", "price": 2999.0},
        headers=headers,
    )
    update_response = client.patch(
        "/api/v1/admin/products/2",
        json={"tags": ["portable"], "specs": {"screen": "11 inch"}},
        headers=headers,
    )
    delete_response = client.delete("/api/v1/admin/products/2", headers=headers)
    detail_response = client.get("/api/v1/admin/products/2", headers=headers)

    assert create_response.status_code == 201
    assert create_response.json()["index_sync_status"] == "attempted"
    assert update_response.status_code == 200
    assert update_response.json()["product"]["tags"] == ["portable"]
    assert delete_response.status_code == 200
    assert detail_response.status_code == 200
    assert detail_response.json()["stock_status"] == "discontinued"


def test_admin_upload_uses_admin_jwt(tmp_path, monkeypatch) -> None:
    client = make_client()
    headers = admin_headers(client)
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))

    response = client.post(
        "/api/v1/admin/upload",
        files={"file": ("product.png", BytesIO(b"fake-png"), "image/png")},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["url"].startswith("/uploads/")
