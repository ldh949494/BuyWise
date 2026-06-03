from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import create_app
from app.models import ChatMessage, ChatSession, Product, Recommendation
from app.schemas.chat import ChatRequest, ProductCard, StructuredNeed
from app.services.chat_service import ChatService


KEYBOARD_CATEGORY = "\u673a\u68b0\u952e\u76d8"
QUIET_TAG = "\u4f4e\u566a\u97f3"
DORM_SCENE = "\u5bbf\u820d"
KEYBOARD_NAME = "K87 \u9759\u97f3\u7ea2\u8f74\u673a\u68b0\u952e\u76d8"
API_MESSAGE = (
    "\u63a8\u8350\u4e00\u4e2a\u5bbf\u820d\u7528\u7684"
    "\u673a\u68b0\u952e\u76d8\uff0c\u9884\u7b97300\u4ee5\u5185\uff0c"
    "\u58f0\u97f3\u5c0f\u4e00\u70b9"
)


class FakeSpeechService:
    async def extract_transcript(self, audio_url: str) -> str:
        return "语音补充：300 元以内"


class FakeVisionService:
    async def extract_image_info(self, image_url: str) -> dict:
        return {"category": "机械键盘", "features": ["低噪音"]}


class FakeIntentService:
    def __init__(self, need: StructuredNeed) -> None:
        self.need = need
        self.calls = []

    async def extract(self, text, image_info=None, history_context=None):
        self.calls.append(
            {
                "text": text,
                "image_info": image_info,
                "history_context": history_context,
            }
        )
        return self.need

    def extract_by_rules(self, text, image_info=None, history_context=None):
        self.calls.append(
            {
                "text": text,
                "image_info": image_info,
                "history_context": history_context,
                "rules_only": True,
            }
        )
        return self.need


class FakeRAGPipeline:
    def __init__(self, products=None, should_fail=False) -> None:
        self.products = products or []
        self.should_fail = should_fail
        self.calls = []

    async def search_products(self, need, db, top_k=20):
        self.calls.append({"need": need, "top_k": top_k})
        if self.should_fail:
            raise RuntimeError("boom")
        return self.products


class FakeRecommendService:
    def rank(self, products, need):
        return [
            ProductCard(
                id=product.id,
                name=product.name,
                price=float(product.price),
                score=90,
                reason="价格符合预算",
            )
            for product in products
        ]


class FakeLLMClient:
    async def generate_clarify_question(self, need):
        return "请补充预算和使用场景。"

    async def stream_clarify_question(self, need):
        yield await self.generate_clarify_question(need)

    async def generate_recommendation(self, need, products):
        return "推荐：" + "、".join(product.name for product in products)

    async def stream_recommendation(self, need, products, **kwargs):
        yield await self.generate_recommendation(need, products)


def make_product(name="K87 静音红轴机械键盘"):
    return Product(
        id=1,
        name=name,
        category="机械键盘",
        price=Decimal("299.00"),
        stock=10,
    )


@pytest.mark.anyio
async def test_handle_chat_returns_clarify_response_when_need_incomplete() -> None:
    need = StructuredNeed(
        intent="商品推荐",
        category="蓝牙耳机",
        need_clarify=True,
        missing_fields=["budget_max", "scenario"],
    )
    intent_service = FakeIntentService(need)
    service = ChatService(
        intent_service=intent_service,
        llm_client=FakeLLMClient(),
    )

    response = await service.handle_chat(ChatRequest(message="推荐一个耳机"), db=object())

    assert response.reply == "请补充预算和使用场景。"
    assert response.need_clarify is True
    assert response.structured_need == need
    assert response.products == []


@pytest.mark.anyio
async def test_handle_chat_runs_multimodal_recommendation_flow() -> None:
    need = StructuredNeed(
        intent="商品推荐",
        category="机械键盘",
        budget_max=300,
        scenario="宿舍",
        preferences=["低噪音"],
    )
    intent_service = FakeIntentService(need)
    product = make_product()
    service = ChatService(
        speech_service=FakeSpeechService(),
        vision_service=FakeVisionService(),
        intent_service=intent_service,
        rag_pipeline=FakeRAGPipeline([product]),
        recommend_service=FakeRecommendService(),
        llm_client=FakeLLMClient(),
    )

    response = await service.handle_chat(
        ChatRequest(message="推荐宿舍用键盘", audio_url="a.wav", image_url="p.jpg"),
        db=object(),
    )

    assert response.reply == "推荐：K87 静音红轴机械键盘"
    assert response.need_clarify is False
    assert response.structured_need == need
    assert response.products[0].name == "K87 静音红轴机械键盘"
    assert "语音补充：300 元以内" in intent_service.calls[0]["text"]
    assert intent_service.calls[0]["image_info"] == {"category": "机械键盘", "features": ["低噪音"]}


@pytest.mark.anyio
async def test_handle_chat_uses_explore_retrieval_for_casual_browse() -> None:
    need = StructuredNeed(
        intent="商品推荐",
        category="机械键盘",
        purchase_stage="browse",
        retrieval_strategy="explore",
    )
    products = [make_product(f"键盘 {index}") for index in range(10)]
    rag_pipeline = FakeRAGPipeline(products)
    service = ChatService(
        intent_service=FakeIntentService(need),
        rag_pipeline=rag_pipeline,
        recommend_service=FakeRecommendService(),
        llm_client=FakeLLMClient(),
    )

    response = await service.handle_chat(ChatRequest(message="随便看看键盘"), db=object())

    assert rag_pipeline.calls[0]["top_k"] == 30
    assert len(response.products) == 8


@pytest.mark.anyio
async def test_handle_chat_uses_strict_retrieval_for_buy_ready_need() -> None:
    need = StructuredNeed(
        intent="商品推荐",
        category="机械键盘",
        budget_max=300,
        scenario="宿舍",
        preferences=["低噪音"],
        purchase_stage="buy_ready",
        retrieval_strategy="strict",
    )
    rag_pipeline = FakeRAGPipeline([make_product()])
    service = ChatService(
        intent_service=FakeIntentService(need),
        rag_pipeline=rag_pipeline,
        recommend_service=FakeRecommendService(),
        llm_client=FakeLLMClient(),
    )

    await service.handle_chat(ChatRequest(message="准备买一个键盘"), db=object())

    assert rag_pipeline.calls[0]["top_k"] == 12


@pytest.mark.anyio
async def test_generate_chat_stream_emits_products_tokens_and_done() -> None:
    need = StructuredNeed(
        intent="商品推荐",
        category="机械键盘",
        budget_max=300,
        scenario="宿舍",
        preferences=["低噪音"],
    )
    service = ChatService(
        intent_service=FakeIntentService(need),
        rag_pipeline=FakeRAGPipeline([make_product()]),
        recommend_service=FakeRecommendService(),
        llm_client=FakeLLMClient(),
    )

    events = [
        event
        async for event in service.generate_chat_stream(
            ChatRequest(session_id="stream-session", message="推荐键盘"),
            db=object(),
        )
    ]

    event_names = [event["event"] for event in events]
    assert event_names[:2] == ["meta", "status"]
    assert "products" in event_names
    assert "token" in event_names
    assert event_names[-1] == "done"
    assert events[0]["data"]["session_id"] == "stream-session"
    assert events[-1]["data"]["reply"]


@pytest.mark.anyio
async def test_generate_chat_stream_fast_products_uses_db_before_rag() -> None:
    need = StructuredNeed(
        intent="商品推荐",
        category="机械键盘",
        budget_max=300,
        need_clarify=True,
        missing_fields=["scenario", "preferences"],
    )
    rag_pipeline = FakeRAGPipeline([make_product("RAG 键盘")])
    service = ChatService(
        intent_service=FakeIntentService(need),
        rag_pipeline=rag_pipeline,
        recommend_service=FakeRecommendService(),
        llm_client=FakeLLMClient(),
    )
    db = _sqlite_session_with_products([make_product("DB 快速键盘")])

    try:
        events = [
            event
            async for event in service.generate_chat_stream(
                ChatRequest(session_id="fast-session", message="推荐一个机械键盘"),
                db=db,
            )
        ]
    finally:
        db.close()

    product_events = [event for event in events if event["event"] == "products"]
    assert product_events[0]["data"]["items"][0]["name"] == "DB 快速键盘"
    assert rag_pipeline.calls == []
    assert any(event["event"] == "token" for event in events)


@pytest.mark.anyio
async def test_generate_chat_stream_fast_products_can_be_disabled() -> None:
    from app.core.config import settings

    settings.chat_stream_fast_products_enabled = False
    need = StructuredNeed(intent="商品推荐", category="机械键盘", budget_max=300)
    rag_pipeline = FakeRAGPipeline([make_product("RAG 键盘")])
    service = ChatService(
        intent_service=FakeIntentService(need),
        rag_pipeline=rag_pipeline,
        recommend_service=FakeRecommendService(),
        llm_client=FakeLLMClient(),
    )
    db = _sqlite_session_with_products([make_product("DB 快速键盘")])

    try:
        events = [
            event
            async for event in service.generate_chat_stream(
                ChatRequest(session_id="full-session", message="推荐一个机械键盘"),
                db=db,
            )
        ]
    finally:
        db.close()

    product_events = [event for event in events if event["event"] == "products"]
    assert product_events[0]["data"]["items"][0]["name"] == "RAG 键盘"
    assert rag_pipeline.calls


@pytest.mark.anyio
async def test_generate_chat_stream_fast_products_falls_back_when_db_empty() -> None:
    need = StructuredNeed(intent="商品推荐", category="机械键盘", budget_max=300)
    rag_pipeline = FakeRAGPipeline([make_product("RAG 兜底键盘")])
    service = ChatService(
        intent_service=FakeIntentService(need),
        rag_pipeline=rag_pipeline,
        recommend_service=FakeRecommendService(),
        llm_client=FakeLLMClient(),
    )
    db = _sqlite_session_with_products([])

    try:
        events = [
            event
            async for event in service.generate_chat_stream(
                ChatRequest(session_id="fallback-session", message="推荐一个机械键盘"),
                db=db,
            )
        ]
    finally:
        db.close()

    product_events = [event for event in events if event["event"] == "products"]
    assert product_events[0]["data"]["items"][0]["name"] == "RAG 兜底键盘"
    assert rag_pipeline.calls


@pytest.mark.anyio
async def test_handle_chat_returns_friendly_error_response() -> None:
    need = StructuredNeed(intent="商品推荐", category="机械键盘", budget_max=300)
    service = ChatService(
        intent_service=FakeIntentService(need),
        rag_pipeline=FakeRAGPipeline(should_fail=True),
        llm_client=FakeLLMClient(),
    )

    response = await service.handle_chat(ChatRequest(message="推荐机械键盘"), db=object())

    assert response.reply == "抱歉，当前暂时无法完成推荐，请稍后再试或换个条件。"
    assert response.need_clarify is False
    assert response.products == []


def test_chat_api_route_is_registered_and_returns_response() -> None:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with session_factory() as db:
        db.add(
            Product(
                name=KEYBOARD_NAME,
                category=KEYBOARD_CATEGORY,
                price=Decimal("299.00"),
                rating=Decimal("4.8"),
                sales=1800,
                tags=[QUIET_TAG],
                suitable_scene=[DORM_SCENE],
                stock=10,
            )
        )
        db.commit()

    app = create_app()

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    response = client.post(
        "/api/v1/ai/chat",
        json={
            "session_id": "s001",
            "message": API_MESSAGE,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["need_clarify"] is False
    assert payload["structured_need"]["category"] == KEYBOARD_CATEGORY
    assert payload["products"][0]["name"] == KEYBOARD_NAME
    assert KEYBOARD_NAME in payload["reply"]
    assert payload["extra"]["session_id"] == "s001"

    with session_factory() as db:
        session = db.scalar(select(ChatSession).where(ChatSession.session_id == "s001"))
        messages = list(db.scalars(select(ChatMessage).where(ChatMessage.session_id == "s001")).all())
        recommendations = list(
            db.scalars(select(Recommendation).where(Recommendation.session_id == "s001")).all()
        )

    assert session is not None
    assert [message.role for message in messages] == ["user", "assistant"]
    assert recommendations
    assert recommendations[0].explanation["budget_match"] is True


def _sqlite_session_with_products(products: list[Product]):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = session_factory()
    db.add_all(products)
    db.commit()
    return db
