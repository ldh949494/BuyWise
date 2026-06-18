from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import create_app


def test_anonymous_chat_session_requires_returned_token(monkeypatch) -> None:
    monkeypatch.setattr(settings, "chat_session_tokens_enabled", True)
    client = _make_client()

    first = client.post("/api/v1/ai/chat", json={"message": "推荐一个键盘"})
    payload = first.json()
    session_id = payload["extra"]["session_id"]
    session_token = payload["extra"]["session_token"]

    forbidden = client.post("/api/v1/ai/chat", json={"session_id": session_id, "message": "继续"})
    allowed = client.post(
        "/api/v1/ai/chat",
        json={"session_id": session_id, "session_token": session_token, "message": "继续"},
    )

    assert forbidden.status_code == 403
    assert allowed.status_code == 200


def _make_client() -> TestClient:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    app = create_app()

    def override_get_db() -> Iterator[Session]:
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)
