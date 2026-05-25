from collections.abc import Iterator
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.traffic import capacity_limited, reset_traffic_state
from app.main import create_app
from app.models import Product
from app.services.chat_service import ChatService


class CapacityLimitedLLM:
    async def chat(self, messages):
        raise capacity_limited("llm")

    async def generate_recommendation(self, need, products):
        raise capacity_limited("llm")


class FakeRAGPipeline:
    async def search_products(self, need, db, top_k=20):
        return [
            Product(
                id=1,
                name="Campus75 三模静音机械键盘",
                category="机械键盘",
                price=Decimal("269.00"),
                stock=10,
            )
        ]


def test_chat_rate_limit_returns_429(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_traffic_state()
    monkeypatch.setattr(settings, "chat_rate_limit_per_minute", 1)
    client = _make_client()

    first = client.post("/api/v1/ai/chat", json={"message": "推荐一个键盘"})
    second = client.post("/api/v1/ai/chat", json={"message": "推荐一个键盘"})

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["code"] == "rate_limited"
    assert second.headers["Retry-After"]


@pytest.mark.anyio
async def test_chat_degrades_when_llm_capacity_is_full() -> None:
    service = ChatService(rag_pipeline=FakeRAGPipeline(), llm_client=CapacityLimitedLLM())

    response = await service.handle_chat(
        request=_chat_request("帮我推荐一个300以内适合宿舍写代码的低噪音机械键盘"),
        db=object(),
    )

    assert response.need_clarify is False
    assert response.products[0].name == "Campus75 三模静音机械键盘"
    assert response.extra["degraded"] is True
    assert response.extra["degraded_reason"] == "llm_capacity_limited"
    assert "AI 总结暂时繁忙" in response.reply


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


def _chat_request(message: str):
    from app.schemas.chat import ChatRequest

    return ChatRequest(message=message)
