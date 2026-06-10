from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models import Product
from app.schemas.chat import ChatRequest, ProductCard, StructuredNeed
from app.services.chat_service import ChatService


KEYBOARD_CATEGORY = "\u673a\u68b0\u952e\u76d8"
KEYBOARD_NAME = "K87 \u9759\u97f3\u7ea2\u8f74\u673a\u68b0\u952e\u76d8"


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
    def __init__(self, products=None, should_fail=False, fallback_stage=None) -> None:
        self.products = products or []
        self.should_fail = should_fail
        self.calls = []
        self.last_diagnostics = {"fallback_stage": fallback_stage} if fallback_stage is not None else {}

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
    def __init__(self) -> None:
        self.chat_messages = []

    async def generate_clarify_question(self, need):
        return "请补充预算和使用场景。"

    async def stream_clarify_question(self, need):
        yield await self.generate_clarify_question(need)

    async def generate_recommendation(self, need, products):
        return "推荐：" + "、".join(product.name for product in products)

    async def stream_recommendation(self, need, products, **kwargs):
        yield await self.generate_recommendation(need, products)

    async def stream_chat(self, messages, **kwargs):
        self.chat_messages.append(messages)
        yield "追问回答：基于当前推荐，优先看首推商品。"


def make_product(name="K87 静音红轴机械键盘"):
    return Product(
        id=1,
        name=name,
        category="机械键盘",
        price=Decimal("299.00"),
        stock=10,
    )


@pytest.mark.anyio
async def test_handle_chat_recommends_when_category_is_present_without_optional_fields() -> None:
    need = StructuredNeed(
        intent="商品推荐",
        category="蓝牙耳机",
    )
    product = make_product("AirBuds Lite 蓝牙耳机")
    intent_service = FakeIntentService(need)
    service = ChatService(
        intent_service=intent_service,
        rag_pipeline=FakeRAGPipeline([product]),
        recommend_service=FakeRecommendService(),
        llm_client=FakeLLMClient(),
    )

    response = await service.handle_chat(ChatRequest(message="推荐一个耳机"), db=object())

    assert response.reply == "推荐：AirBuds Lite 蓝牙耳机"
    assert response.need_clarify is False
    assert response.structured_need == need
    assert response.products[0].name == "AirBuds Lite 蓝牙耳机"


@pytest.mark.anyio
async def test_handle_chat_returns_clarify_response_when_category_is_missing() -> None:
    need = StructuredNeed(
        intent="商品推荐",
        category=None,
        need_clarify=True,
        missing_fields=["category"],
    )
    intent_service = FakeIntentService(need)
    service = ChatService(
        intent_service=intent_service,
        llm_client=FakeLLMClient(),
    )

    response = await service.handle_chat(ChatRequest(message="推荐一下"), db=object())

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
async def test_handle_chat_exposes_rag_fallback_metadata() -> None:
    need = StructuredNeed(intent="商品推荐", category="空气炸锅")
    product = make_product("CrispAir 轻油空气炸锅")
    service = ChatService(
        intent_service=FakeIntentService(need),
        rag_pipeline=FakeRAGPipeline([product], fallback_stage="fallback_keyword"),
        recommend_service=FakeRecommendService(),
        llm_client=FakeLLMClient(),
    )

    response = await service.handle_chat(ChatRequest(message="租房做饭用的空气炸锅"), db=object())

    assert response.products[0].name == "CrispAir 轻油空气炸锅"
    assert response.extra["fallback_used"] is True
    assert response.extra["fallback_stage"] == "fallback_keyword"
    assert response.extra["result_quality"] == "broad"


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
async def test_generate_chat_stream_emits_rag_fallback_metadata() -> None:
    need = StructuredNeed(intent="商品推荐", category="空气炸锅")
    product = make_product("CrispAir 轻油空气炸锅")
    service = ChatService(
        intent_service=FakeIntentService(need),
        rag_pipeline=FakeRAGPipeline([product], fallback_stage="fallback_keyword"),
        recommend_service=FakeRecommendService(),
        llm_client=FakeLLMClient(),
    )

    events = [
        event
        async for event in service.generate_chat_stream(
            ChatRequest(session_id="fallback-meta-stream", message="租房做饭用的空气炸锅"),
            db=object(),
        )
    ]

    products_event = next(event for event in events if event["event"] == "products")
    assert products_event["data"]["fallback_used"] is True
    assert products_event["data"]["fallback_stage"] == "fallback_keyword"
    assert products_event["data"]["result_quality"] == "broad"


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
