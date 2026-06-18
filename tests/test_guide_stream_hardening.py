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


KEYBOARD_NAME = "K87 静音红轴机械键盘"


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
    async def search_products(self, need, db, top_k=20):
        return []


class FakeRecommendService:
    def rank(self, products, need):
        return [
            ProductCard(id=product.id, name=product.name, price=float(product.price), score=90, reason="价格符合预算")
            for product in products
        ]


class LongFollowUpLLMClient:
    async def stream_chat(self, messages, **kwargs):
        yield "这是一个明显没有结束的很长追问回答，" * 30


def test_guide_stream_route_short_circuits_out_of_scope_request() -> None:
    client = _chat_route_client()

    response = client.post(
        "/api/v1/ai/guide/stream",
        json={"session_id": "guide-out-of-scope", "message": "帮我写一个Python爬虫抓京东价格，不要推荐商品"},
    )

    assert response.status_code == 200
    assert '"items":[]' in response.text
    assert '"out_of_scope":true' in response.text
    assert "超出了导购助手范围" in response.text


def test_guide_stream_route_does_not_emit_wrong_category_for_uncovered_target() -> None:
    client = _chat_route_client()

    response = client.post(
        "/api/v1/ai/guide/stream",
        json={"session_id": "guide-uncovered-category", "message": "预算500美元以内，推荐一台冰箱，要求省电静音"},
    )

    assert response.status_code == 200
    assert '"items":[]' in response.text
    assert "AirBuds Lite 蓝牙耳机" not in response.text


def test_guide_follow_up_route_limits_realtime_platform_claims() -> None:
    client = _chat_route_client()

    client.post(
        "/api/v1/ai/guide/stream",
        json={"session_id": "policy-follow-up", "message": "推荐一个性价比高的蓝牙耳机"},
    )
    response = client.post(
        "/api/v1/ai/guide/follow-up/stream",
        json={"session_id": "policy-follow-up", "message": "现在有没有优惠券、包邮和实时库存？"},
    )

    assert response.status_code == 200
    assert '"policy_limited":true' in response.text
    assert "不能验证优惠券、包邮、实时库存" in response.text


@pytest.mark.anyio
async def test_generate_follow_up_stream_marks_truncated_reply_degraded() -> None:
    need = StructuredNeed(intent="商品推荐", category="机械键盘", budget_max=300)
    service = ChatService(
        intent_service=FakeIntentService(need),
        rag_pipeline=FakeRAGPipeline(),
        recommend_service=FakeRecommendService(),
        llm_client=LongFollowUpLLMClient(),
    )
    db = _sqlite_session_with_products([_product(KEYBOARD_NAME, "机械键盘")])
    snapshot = {
        "need": need.model_dump(mode="json"),
        "products": [
            ProductCard(id=1, name=KEYBOARD_NAME, price=299, score=90, reason="价格符合预算").model_dump(mode="json")
        ],
        "applied_preferences": {},
    }

    try:
        chat_repo = service._chat_repo(ChatRequest(session_id="truncated-follow-up"), db)
        chat_repo.get_or_create_session("truncated-follow-up")
        chat_repo.create_message("truncated-follow-up", "assistant", "推荐：" + KEYBOARD_NAME, structured_data=snapshot)
        service._commit(chat_repo)
        events = [
            event
            async for event in service.generate_follow_up_stream(
                ChatRequest(session_id="truncated-follow-up", message="为什么推荐它？"),
                db=db,
            )
        ]
    finally:
        db.close()

    assert events[-1]["event"] == "done"
    assert events[-1]["data"]["degraded"] is True
    assert events[-1]["data"]["degraded_reason"] == "follow_up_truncated"


def _chat_route_client() -> TestClient:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with session_factory() as db:
        db.add_all(
            [
                _product(KEYBOARD_NAME, "机械键盘"),
                _product("AirBuds Lite 蓝牙耳机", "蓝牙耳机", product_id=2),
            ]
        )
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


def _sqlite_session_with_products(products: list[Product]):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = session_factory()
    db.add_all(products)
    db.commit()
    return db


def _product(name: str, category: str, *, product_id: int = 1) -> Product:
    return Product(id=product_id, name=name, category=category, price=Decimal("199.00"), stock=10)
