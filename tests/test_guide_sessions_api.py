from fastapi.testclient import TestClient
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.config import settings
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


def test_anonymous_guide_session_list_does_not_expose_remote_sessions_when_tokens_enabled(monkeypatch) -> None:
    monkeypatch.setattr(settings, "chat_session_tokens_enabled", True)
    client = make_client()

    first = client.post("/api/v1/ai/guide/stream", json={"message": "推荐一个键盘"})
    listed = client.get("/api/v1/ai/guide/sessions")

    assert first.status_code == 200
    assert listed.status_code == 200
    assert listed.json()["items"] == []


def test_anonymous_guide_session_detail_requires_token_when_tokens_enabled(monkeypatch) -> None:
    monkeypatch.setattr(settings, "chat_session_tokens_enabled", True)
    client = make_client()

    first = client.post("/api/v1/ai/guide/stream", json={"message": "推荐一个键盘"})
    events = _sse_events(first.text)
    meta = next(event for event in events if event["event"] == "meta")["data"]
    session_id = meta["session_id"]
    session_token = meta["session_token"]

    forbidden = client.get(f"/api/v1/ai/guide/sessions/{session_id}")
    allowed = client.get(f"/api/v1/ai/guide/sessions/{session_id}", params={"session_token": session_token})

    assert forbidden.status_code == 403
    assert allowed.status_code == 200
    assert [message["role"] for message in allowed.json()["messages"][:2]] == ["user", "assistant"]


def test_user_guide_session_list_and_detail_still_work_when_tokens_enabled(monkeypatch) -> None:
    monkeypatch.setattr(settings, "chat_session_tokens_enabled", True)
    client = make_client()
    headers = _user_headers(client)

    first = client.post("/api/v1/ai/guide/stream", json={"message": "推荐一个键盘"}, headers=headers)
    session_id = next(event for event in _sse_events(first.text) if event["event"] == "meta")["data"]["session_id"]
    listed = client.get("/api/v1/ai/guide/sessions", headers=headers)
    detail = client.get(f"/api/v1/ai/guide/sessions/{session_id}", headers=headers)

    assert first.status_code == 200
    assert listed.status_code == 200
    assert [item["session_id"] for item in listed.json()["items"]] == [session_id]
    assert detail.status_code == 200
    assert [message["role"] for message in detail.json()["messages"][:2]] == ["user", "assistant"]


def _user_headers(client: TestClient) -> dict[str, str]:
    client.post("/api/v1/auth/otp/request", json={"phone": "13812345678"})
    login = client.post("/api/v1/auth/otp/verify", json={"phone": "13812345678", "code": "123456"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _sse_events(text: str) -> list[dict]:
    events = []
    event = None
    data_lines = []
    for line in text.splitlines():
        if line.startswith("event: "):
            event = line.removeprefix("event: ")
        elif line.startswith("data: "):
            data_lines.append(line.removeprefix("data: "))
        elif not line and event is not None:
            import json

            events.append({"event": event, "data": json.loads("\n".join(data_lines))})
            event = None
            data_lines = []
    return events
