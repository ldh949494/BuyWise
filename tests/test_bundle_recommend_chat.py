from decimal import Decimal

import pytest

from app.models import Product
from app.schemas.chat import ChatRequest, ProductCard, StructuredNeed
from app.services.chat_service import ChatService


class FakeIntentService:
    def __init__(self, need: StructuredNeed) -> None:
        self.need = need

    async def extract(self, text, image_info=None, history_context=None):
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
            ProductCard(
                id=product.id,
                name=product.name,
                price=float(product.price),
                score=90,
                reason="适合组合方案",
            )
            for product in products
        ]


class FakeLLMClient:
    async def generate_recommendation(self, need, products):
        return "推荐：" + "、".join(product.name for product in products)


def make_bundle_product(product_id, name, category, price):
    return Product(id=product_id, name=name, category=category, price=Decimal(str(price)), stock=10)


@pytest.mark.anyio
async def test_handle_chat_builds_bundle_recommendation_from_existing_chat_contract() -> None:
    need = StructuredNeed(
        intent="场景化组合推荐",
        budget_max=700,
        scenario="旅行",
        preferences=["轻便"],
        avoid=["大容量"],
    )
    rag_pipeline = FakeRAGPipeline(
        [
            make_bundle_product(1, "轻薄充电宝", "充电宝", 129),
            make_bundle_product(2, "轻量双肩包", "双肩包", 239),
            make_bundle_product(3, "通勤降噪耳机", "蓝牙耳机", 299),
            make_bundle_product(4, "备用充电宝", "充电宝", 159),
        ]
    )
    service = ChatService(
        intent_service=FakeIntentService(need),
        rag_pipeline=rag_pipeline,
        recommend_service=FakeRecommendService(),
        llm_client=FakeLLMClient(),
    )

    response = await service.handle_chat(ChatRequest(message="搭配一套旅行装备"), db=object())

    assert response.need_clarify is False
    assert response.structured_need == need
    assert [product.name for product in response.products] == ["轻薄充电宝", "轻量双肩包", "通勤降噪耳机"]
    assert sum(product.price for product in response.products) <= 700
    assert rag_pipeline.calls[0]["top_k"] == 30
