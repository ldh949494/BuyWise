from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import create_app


def make_client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    app = create_app()

    def override_get_db():
        session = testing_session_local()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def auth_headers(client: TestClient) -> dict[str, str]:
    client.post("/api/v1/auth/otp/request", json={"phone": "13812345678"})
    login = client.post("/api/v1/auth/otp/verify", json={"phone": "13812345678", "code": "123456"}).json()
    return {"Authorization": f"Bearer {login['access_token']}"}


def test_guide_preferences_crud_requires_user_auth() -> None:
    client = make_client()

    unauthenticated = client.get("/api/v1/guide/preferences")

    assert unauthenticated.status_code == 401


def test_guide_preferences_crud_round_trip() -> None:
    client = make_client()
    headers = auth_headers(client)

    payload = {
        "budget_policy": "strict",
        "presentation_style": "compare_options",
        "single_item_budgets": {"机械键盘": {"min": 200, "max": 500}},
        "bundle_budget_range": {"min": 3000, "max": 6000},
        "priority_tags": ["静音", "静音", "耐用"],
        "excluded_tags": ["RGB"],
        "excluded_brands": ["BrandX"],
        "owned_categories": ["显示器"],
        "extra_notes": "宿舍桌面小",
    }

    saved = client.put("/api/v1/guide/preferences", json=payload, headers=headers)
    loaded = client.get("/api/v1/guide/preferences", headers=headers)
    deleted = client.delete("/api/v1/guide/preferences", headers=headers)
    reset = client.get("/api/v1/guide/preferences", headers=headers)

    assert saved.status_code == 200
    assert saved.json()["has_saved_preferences"] is True
    assert saved.json()["priority_tags"] == ["静音", "耐用"]
    assert loaded.json()["owned_categories"] == ["显示器"]
    assert deleted.status_code == 204
    assert reset.json()["has_saved_preferences"] is False
