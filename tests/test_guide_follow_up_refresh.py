import pytest

from app.schemas.chat import ChatRequest, ProductCard, StructuredNeed
from app.services.chat_service import ChatService
from app.services.intent_service import IntentService
from tests.test_guide_stream_api import (
    DORM_SCENE,
    KEYBOARD_CATEGORY,
    KEYBOARD_NAME,
    QUIET_TAG,
    FakeLLMClient,
    FakeRAGPipeline,
    FakeRecommendService,
    _sqlite_session_with_products,
    make_product,
)


@pytest.mark.anyio
async def test_generate_follow_up_stream_refreshes_when_budget_changes() -> None:
    need = StructuredNeed(
        intent="商品推荐",
        category=KEYBOARD_CATEGORY,
        budget_max=300,
        scenario=DORM_SCENE,
        preferences=[QUIET_TAG],
    )
    service = ChatService(
        intent_service=IntentService(),
        rag_pipeline=FakeRAGPipeline([]),
        recommend_service=FakeRecommendService(),
        llm_client=FakeLLMClient(),
    )
    db = _sqlite_session_with_products([make_product()])
    snapshot = {
        "need": need.model_dump(mode="json"),
        "products": [
            ProductCard(id=1, name=KEYBOARD_NAME, price=299, score=90, reason="价格符合预算").model_dump(mode="json")
        ],
        "applied_preferences": {},
    }

    try:
        chat_repo = service._chat_repo(ChatRequest(session_id="follow-budget-refresh"), db)
        chat_repo.get_or_create_session("follow-budget-refresh")
        chat_repo.create_message("follow-budget-refresh", "assistant", "推荐：" + KEYBOARD_NAME, structured_data=snapshot)
        service._commit(chat_repo)
        events = [
            event
            async for event in service.generate_follow_up_stream(
                ChatRequest(session_id="follow-budget-refresh", message="预算改到500"),
                db=db,
            )
        ]
    finally:
        db.close()

    product_events = [event for event in events if event["event"] == "products"]
    assert product_events
    assert product_events[-1]["data"]["structured_need"]["budget_max"] == 500
    assert events[-1]["event"] == "done"
    assert events[-1]["data"]["should_refresh"] is False
    assert events[-1]["data"]["extra"]["turn_type"] == "refresh_recommendation"


@pytest.mark.anyio
async def test_generate_follow_up_stream_refreshes_when_chinese_budget_regenerates() -> None:
    need = StructuredNeed(
        intent="商品推荐",
        category=KEYBOARD_CATEGORY,
        budget_max=300,
        scenario=DORM_SCENE,
        preferences=[QUIET_TAG],
    )
    service = ChatService(
        intent_service=IntentService(),
        rag_pipeline=FakeRAGPipeline([]),
        recommend_service=FakeRecommendService(),
        llm_client=FakeLLMClient(),
    )
    db = _sqlite_session_with_products([make_product()])
    snapshot = {
        "need": need.model_dump(mode="json"),
        "products": [
            ProductCard(id=1, name=KEYBOARD_NAME, price=299, score=90, reason="价格符合预算").model_dump(mode="json")
        ],
        "applied_preferences": {},
    }

    try:
        chat_repo = service._chat_repo(ChatRequest(session_id="follow-chinese-budget-refresh"), db)
        chat_repo.get_or_create_session("follow-chinese-budget-refresh")
        chat_repo.create_message("follow-chinese-budget-refresh", "assistant", "推荐：" + KEYBOARD_NAME, structured_data=snapshot)
        service._commit(chat_repo)
        events = [
            event
            async for event in service.generate_follow_up_stream(
                ChatRequest(session_id="follow-chinese-budget-refresh", message="如果提高预算到五百元，请帮我重新生成推荐"),
                db=db,
            )
        ]
    finally:
        db.close()

    product_events = [event for event in events if event["event"] == "products"]
    assert product_events
    assert product_events[-1]["data"]["structured_need"]["budget_max"] == 500
    assert events[-1]["event"] == "done"
    assert events[-1]["data"]["should_refresh"] is False
    assert events[-1]["data"]["extra"]["turn_type"] == "refresh_recommendation"
