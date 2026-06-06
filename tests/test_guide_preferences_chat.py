from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models import UserGuidePreferences
from app.schemas.chat import ChatRequest, StructuredNeed
from app.services.chat_service import ChatService


class FakeIntentService:
    def __init__(self, need):
        self.need = need

    async def extract(self, text, image_info=None, history_context=None):
        return self.need


class FakeRAGPipeline:
    async def search_products(self, need, db, top_k=20):
        return [
            SimpleNamespace(
                id=1,
                name="Silent K87 机械键盘",
                price=520,
                image_url=None,
                rating=4.7,
                tags=["静音", "耐用"],
                suitable_scene=["宿舍"],
                specs={},
                stock=10,
                stock_status="in_stock",
            )
        ]


class FakeLLM:
    async def generate_recommendation(self, need, products):
        return "推荐 Silent K87"

    async def generate_clarify_question(self, need):
        return "请补充预算"


@pytest.mark.anyio
async def test_chat_applies_saved_guide_preferences() -> None:
    db = make_db()
    db.add(
        UserGuidePreferences(
            user_id=1,
            budget_policy="slightly_flexible",
            presentation_style="compare_options",
            preferences_json={
                "single_item_budgets": {"机械键盘": {"min": 200, "max": 500}},
                "priority_tags": ["静音"],
                "excluded_tags": [],
                "excluded_brands": [],
                "owned_categories": [],
                "bundle_budget_range": None,
                "extra_notes": None,
            },
        )
    )
    db.commit()
    service = ChatService(
        intent_service=FakeIntentService(StructuredNeed(intent="商品推荐", category="机械键盘", scenario="宿舍")),
        rag_pipeline=FakeRAGPipeline(),
        llm_client=FakeLLM(),
    )

    response = await service.handle_chat(ChatRequest(message="推荐一个键盘"), db, user_id=1)

    assert response.structured_need.budget_max == 500
    assert "静音" in response.structured_need.preferences
    assert response.applied_preferences.used_saved_preferences is True
    assert "允许小幅超预算" in response.applied_preferences.summary


@pytest.mark.anyio
async def test_chat_can_ignore_saved_guide_preferences() -> None:
    db = make_db()
    db.add(
        UserGuidePreferences(
            user_id=1,
            budget_policy="strict",
            presentation_style="compare_options",
            preferences_json={"single_item_budgets": {"机械键盘": {"max": 300}}},
        )
    )
    db.commit()
    service = ChatService(
        intent_service=FakeIntentService(StructuredNeed(intent="商品推荐", category="机械键盘")),
        rag_pipeline=FakeRAGPipeline(),
        llm_client=FakeLLM(),
    )

    response = await service.handle_chat(ChatRequest(message="推荐一个键盘", ignore_saved_preferences=True), db, user_id=1)

    assert response.structured_need.budget_max is None
    assert response.applied_preferences.used_saved_preferences is False
    assert response.applied_preferences.ignored_saved_preferences is True


def make_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()
