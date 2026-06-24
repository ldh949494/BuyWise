from fastapi.testclient import TestClient
from decimal import Decimal
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
        db.add(Product(id=1, name="History K87 静音键盘", category="机械键盘", price=Decimal("299.00"), tags=["静音"], stock_status="in_stock"))
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


def test_create_and_restore_guide_session_without_messages() -> None:
    client = make_client()

    created = client.post("/api/v1/ai/guide/sessions")
    payload = created.json()
    detail = client.get(f"/api/v1/ai/guide/sessions/{payload['session_id']}")

    assert created.status_code == 200
    assert payload["session_id"]
    assert detail.status_code == 200
    assert detail.json()["session_id"] == payload["session_id"]
    assert detail.json()["messages"] == []


def test_guide_session_detail_returns_renderable_messages() -> None:
    client = make_client()
    session_id = "history-render-session"

    client.post("/api/v1/ai/guide/stream", json={"session_id": session_id, "message": "推荐一个键盘"})
    detail = client.get(f"/api/v1/ai/guide/sessions/{session_id}")

    assert detail.status_code == 200
    messages = detail.json()["messages"]
    assert [message["role"] for message in messages[:2]] == ["user", "assistant"]
    assert messages[1]["products"] or messages[1]["bundle_plans"]


def test_guide_session_list_returns_recent_sessions() -> None:
    client = make_client()

    client.post("/api/v1/ai/guide/stream", json={"session_id": "history-list-session", "message": "推荐一个键盘"})
    listed = client.get("/api/v1/ai/guide/sessions")

    assert listed.status_code == 200
    assert listed.json()["items"][0]["session_id"] == "history-list-session"
