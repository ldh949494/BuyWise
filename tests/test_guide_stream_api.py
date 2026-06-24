from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.dependencies import AppContainerBuilder
from app.core.database import Base, get_db
from app.main import create_app
from app.models import Product
from app.schemas.chat import ChatRequest, ProductCard, StructuredNeed
from app.services.chat_service import ChatService
from app.services.intent_service import IntentService


KEYBOARD_CATEGORY = "机械键盘"
QUIET_TAG = "低噪音"
DORM_SCENE = "宿舍"
KEYBOARD_NAME = "K87 静音红轴机械键盘"
API_MESSAGE = "推荐一个宿舍用的机械键盘，预算300以内，声音小一点"
CATEGORY_ONLY_GUIDE_CASES = [
    ("guide-category-keyboard", "我需要一个键盘", "机械键盘", "K87 静音红轴机械键盘"),
    ("guide-category-earbuds", "我需要一个耳机", "蓝牙耳机", "AirBuds Lite 蓝牙耳机"),
    ("guide-category-powerbank", "我需要一个充电宝", "充电宝", "PowerMax 轻薄快充充电宝"),
    ("guide-category-backpack", "我需要一个书包", "双肩包", "CityPack 通勤双肩包"),
    ("guide-category-lamp", "我需要一个台灯", "台灯", "StudyLamp Pro 护眼台灯"),
    ("guide-category-mouse", "我需要一个鼠标", "鼠标", "QuietMouse M1 静音鼠标"),
]


class EmptyProductStore:
    def search(self, query: str, top_k: int = 10) -> list[dict]:
        return []

    def count(self) -> int:
        return 0

    def indexed_product_ids(self) -> list[int]:
        return []


class FakeIntentService:
    def __init__(self, need: StructuredNeed) -> None:
        self.need = need

    async def extract(self, text, image_info=None, history_context=None):
        return self.need

    def extract_by_rules(self, text, image_info=None, history_context=None):
        return self.need


class FakeRAGPipeline:
    def __init__(self, products=None) -> None:
        self.products = products or []
        self.calls = []

    async def search_products(self, need, db, top_k=20):
        self.calls.append({"need": need, "top_k": top_k})
        return self.products


class FakeRecommendService:
    def rank(self, products, need):
        return [
            ProductCard(id=product.id, name=product.name, price=float(product.price), score=90, reason="价格符合预算")
            for product in products
        ]


class FakeLLMClient:
    def __init__(self) -> None:
        self.chat_messages = []

    async def stream_recommendation(self, need, products, **kwargs):
        yield "推荐：" + "、".join(product.name for product in products)

    async def stream_clarify_question(self, need):
        yield "请补充预算和使用场景。"

    async def stream_chat(self, messages, **kwargs):
        self.chat_messages.append(messages)
        yield "追问回答：基于当前推荐，优先看首推商品。"


def make_product(
    name=KEYBOARD_NAME,
    *,
    product_id: int = 1,
    category: str = KEYBOARD_CATEGORY,
    price: Decimal = Decimal("299.00"),
):
    return Product(id=product_id, name=name, category=category, price=price, stock=10)


@pytest.mark.anyio
async def test_generate_guide_stream_emits_fast_products_before_full_recommendation() -> None:
    need = StructuredNeed(intent="商品推荐", category=KEYBOARD_CATEGORY, budget_max=300)
    rag_pipeline = FakeRAGPipeline([make_product("RAG 慢导购键盘")])
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
            async for event in service.generate_guide_stream(
                ChatRequest(session_id="guide-session", message="推荐一个机械键盘"),
                db=db,
            )
        ]
    finally:
        db.close()

    product_events = [event for event in events if event["event"] == "products"]
    assert product_events[0]["data"]["items"][0]["name"] == "DB 快速键盘"
    assert product_events[0]["data"]["provisional"] is True
    assert product_events[0]["data"]["source"] == "fast_db"
    assert product_events[-1]["data"]["items"][0]["name"] == "RAG 慢导购键盘"
    assert product_events[-1]["data"]["provisional"] is False
    assert product_events[-1]["data"]["source"] == "rag"
    assert rag_pipeline.calls


@pytest.mark.anyio
async def test_generate_guide_stream_skips_empty_fast_products_event_when_db_has_no_match() -> None:
    need = StructuredNeed(intent="商品推荐", category=KEYBOARD_CATEGORY, budget_max=300)
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
            async for event in service.generate_guide_stream(
                ChatRequest(session_id="guide-empty-fast-session", message="推荐一个机械键盘"),
                db=db,
            )
        ]
    finally:
        db.close()

    product_events = [event for event in events if event["event"] == "products"]
    assert len(product_events) == 1
    assert product_events[0]["data"]["items"][0]["name"] == "RAG 兜底键盘"
    assert product_events[0]["data"]["provisional"] is False
    assert product_events[0]["data"]["source"] == "rag"
    assert rag_pipeline.calls


@pytest.mark.anyio
async def test_generate_guide_stream_promotes_fast_products_when_final_rag_is_empty() -> None:
    need = StructuredNeed(intent="商品推荐", category=KEYBOARD_CATEGORY, budget_max=300)
    service = ChatService(
        intent_service=FakeIntentService(need),
        rag_pipeline=FakeRAGPipeline([]),
        recommend_service=FakeRecommendService(),
        llm_client=FakeLLMClient(),
    )
    db = _sqlite_session_with_products([make_product("DB 兜底键盘")])

    try:
        events = [
            event
            async for event in service.generate_guide_stream(
                ChatRequest(session_id="guide-final-empty-session", message="推荐一个机械键盘"),
                db=db,
            )
        ]
    finally:
        db.close()

    product_events = [event for event in events if event["event"] == "products"]
    assert product_events[0]["data"]["provisional"] is True
    assert product_events[-1]["data"]["items"][0]["name"] == "DB 兜底键盘"
    assert product_events[-1]["data"]["provisional"] is False
    assert product_events[-1]["data"]["source"] == "fallback"
    assert product_events[-1]["data"]["fallback_stage"] == "fast_db_final_fallback"


@pytest.mark.anyio
async def test_generate_follow_up_stream_uses_saved_snapshot_without_rag() -> None:
    need = StructuredNeed(intent="商品推荐", category=KEYBOARD_CATEGORY, budget_max=300)
    rag_pipeline = FakeRAGPipeline([make_product("不应检索键盘")])
    llm_client = FakeLLMClient()
    service = ChatService(
        intent_service=FakeIntentService(need),
        rag_pipeline=rag_pipeline,
        recommend_service=FakeRecommendService(),
        llm_client=llm_client,
    )
    db = _sqlite_session_with_products([])
    snapshot = {
        "need": need.model_dump(mode="json"),
        "products": [
            ProductCard(id=1, name=KEYBOARD_NAME, price=299, score=90, reason="价格符合预算").model_dump(mode="json")
        ],
        "applied_preferences": {},
    }

    try:
        chat_repo = service._chat_repo(ChatRequest(session_id="follow-session"), db)
        chat_repo.get_or_create_session("follow-session")
        chat_repo.create_message("follow-session", "assistant", "推荐：" + KEYBOARD_NAME, structured_data=snapshot)
        service._commit(chat_repo)
        events = [
            event
            async for event in service.generate_follow_up_stream(
                ChatRequest(session_id="follow-session", message="为什么推荐它？"),
                db=db,
            )
        ]
    finally:
        db.close()

    assert rag_pipeline.calls == []
    assert any(event["event"] == "token" for event in events)
    assert events[-1]["data"]["should_refresh"] is False
    assert KEYBOARD_NAME in llm_client.chat_messages[0][1]["content"]


@pytest.mark.anyio
async def test_generate_follow_up_stream_explanation_keeps_snapshot_context() -> None:
    need = StructuredNeed(intent="商品推荐", category=KEYBOARD_CATEGORY, budget_max=300)
    llm_client = FakeLLMClient()
    service = ChatService(
        intent_service=FakeIntentService(need),
        rag_pipeline=FakeRAGPipeline([]),
        recommend_service=FakeRecommendService(),
        llm_client=llm_client,
    )
    db = _sqlite_session_with_products([])
    snapshot = {
        "need": need.model_dump(mode="json"),
        "products": [
            ProductCard(id=1, name=KEYBOARD_NAME, price=299, score=90, reason="价格符合预算").model_dump(mode="json")
        ],
        "applied_preferences": {},
    }

    try:
        chat_repo = service._chat_repo(ChatRequest(session_id="follow-explain-snapshot"), db)
        chat_repo.get_or_create_session("follow-explain-snapshot")
        chat_repo.create_message("follow-explain-snapshot", "assistant", "推荐：" + KEYBOARD_NAME, structured_data=snapshot)
        service._commit(chat_repo)
        events = [
            event
            async for event in service.generate_follow_up_stream(
                ChatRequest(session_id="follow-explain-snapshot", message="为什么推荐它？"),
                db=db,
            )
        ]
    finally:
        db.close()

    assert [event["event"] for event in events][:2] == ["meta", "status"]
    assert events[-1]["event"] == "done"
    assert events[-1]["data"]["should_refresh"] is False
    assert llm_client.chat_messages
    assert KEYBOARD_NAME in llm_client.chat_messages[0][1]["content"]


@pytest.mark.anyio
async def test_generate_follow_up_stream_returns_refresh_signal_without_snapshot() -> None:
    service = ChatService(llm_client=FakeLLMClient())
    db = _sqlite_session_with_products([])

    try:
        events = [
            event
            async for event in service.generate_follow_up_stream(
                ChatRequest(session_id="empty-session", message="为什么推荐它？"),
                db=db,
            )
        ]
    finally:
        db.close()

    assert events[-1]["event"] == "done"
    assert events[-1]["data"]["should_refresh"] is True
    assert events[-1]["data"]["refresh_reason"] == "missing_recommendation_snapshot"


@pytest.mark.anyio
async def test_generate_follow_up_stream_returns_cart_action_payload() -> None:
    need = StructuredNeed(intent="商品推荐", category=KEYBOARD_CATEGORY, budget_max=300)
    service = ChatService(
        intent_service=FakeIntentService(need),
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
        chat_repo = service._chat_repo(ChatRequest(session_id="cart-action-follow-up"), db)
        chat_repo.get_or_create_session("cart-action-follow-up")
        chat_repo.create_message("cart-action-follow-up", "assistant", "推荐：" + KEYBOARD_NAME, structured_data=snapshot)
        service._commit(chat_repo)
        events = [
            event
            async for event in service.generate_follow_up_stream(
                ChatRequest(session_id="cart-action-follow-up", message="把刚才那款加到购物车"),
                db=db,
            )
        ]
    finally:
        db.close()

    assert events[-1]["event"] == "done"
    assert events[-1]["data"]["extra"]["action"] == "cart.add"
    assert events[-1]["data"]["extra"]["cart"]["items"][0]["product_id"] == 1
    assert "已加入购物车" in events[-1]["data"]["reply"]


def test_guide_stream_route_is_registered_and_streams_sse() -> None:
    client = _chat_route_client()

    response = client.post("/api/v1/ai/guide/stream", json={"session_id": "guide-route", "message": API_MESSAGE})

    assert response.status_code == 200
    assert "event: meta" in response.text
    assert "event: products" in response.text
    assert KEYBOARD_NAME in response.text


def test_guide_stream_route_returns_products_for_category_only_requests() -> None:
    client = _chat_route_client(_category_only_products())

    for session_id, message, category, product_name in CATEGORY_ONLY_GUIDE_CASES:
        response = client.post("/api/v1/ai/guide/stream", json={"session_id": session_id, "message": message})

        assert response.status_code == 200
        assert '"need_clarify":false' in response.text
        assert f'"category":"{category}"' in response.text
        assert product_name in response.text


def test_guide_follow_up_route_uses_snapshot_after_category_only_start() -> None:
    client = _chat_route_client(_category_only_products())

    start_response = client.post(
        "/api/v1/ai/guide/stream",
        json={"session_id": "category-follow-up", "message": "我需要一个键盘"},
    )
    follow_up_response = client.post(
        "/api/v1/ai/guide/follow-up/stream",
        json={"session_id": "category-follow-up", "message": "为什么推荐它？"},
    )

    assert start_response.status_code == 200
    assert KEYBOARD_NAME in start_response.text
    assert follow_up_response.status_code == 200
    assert '"should_refresh":false' in follow_up_response.text
    assert KEYBOARD_NAME in follow_up_response.text


def test_guide_stream_route_explains_when_no_matching_products() -> None:
    client = _chat_route_client([])

    response = client.post(
        "/api/v1/ai/guide/stream",
        json={"session_id": "guide-empty-products", "message": "我需要一个键盘"},
    )

    assert response.status_code == 200
    assert "event: products" in response.text
    assert '"items":[]' in response.text
    assert "没有找到匹配商品" in response.text


def test_guide_follow_up_route_returns_refresh_signal_without_snapshot() -> None:
    client = _chat_route_client()

    response = client.post(
        "/api/v1/ai/guide/follow-up/stream",
        json={"session_id": "missing-follow-up", "message": "为什么推荐它？"},
    )

    assert response.status_code == 200
    assert "event: done" in response.text
    assert '"should_refresh":true' in response.text
    assert '"refresh_reason":"missing_recommendation_snapshot"' in response.text


def _chat_route_client(products: list[Product] | None = None) -> TestClient:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with session_factory() as db:
        db.add_all(products if products is not None else [_route_keyboard_product()])
        db.commit()

    app = create_app(AppContainerBuilder().with_product_store(EmptyProductStore()))

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def _route_keyboard_product() -> Product:
    return Product(
        name=KEYBOARD_NAME,
        category=KEYBOARD_CATEGORY,
        price=Decimal("299.00"),
        rating=Decimal("4.8"),
        sales=1800,
        tags=[QUIET_TAG],
        suitable_scene=[DORM_SCENE],
        stock=10,
    )


def _category_only_products() -> list[Product]:
    return [
        _route_keyboard_product(),
        make_product("AirBuds Lite 蓝牙耳机", product_id=2, category="蓝牙耳机", price=Decimal("199.00")),
        make_product("PowerMax 轻薄快充充电宝", product_id=3, category="充电宝", price=Decimal("139.00")),
        make_product("CityPack 通勤双肩包", product_id=4, category="双肩包", price=Decimal("259.00")),
        make_product("StudyLamp Pro 护眼台灯", product_id=5, category="台灯", price=Decimal("229.00")),
        make_product("QuietMouse M1 静音鼠标", product_id=6, category="鼠标", price=Decimal("89.00")),
    ]


def _sqlite_session_with_products(products: list[Product]):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = session_factory()
    db.add_all(products)
    db.commit()
    return db
