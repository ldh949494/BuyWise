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
        intent="bundle_recommend",
        budget_max=6000,
        scenario="桌面",
        preferences=["办公"],
    )
    rag_pipeline = FakeRAGPipeline(
        [
            make_bundle_product(1, "DeskMini S 入门迷你主机", "电脑", 2599),
            make_bundle_product(2, "ClearView 24 护眼显示器", "显示器", 799),
            make_bundle_product(3, "Campus75 三模静音机械键盘", "机械键盘", 289),
            make_bundle_product(4, "QuietMouse M1 静音办公鼠标", "鼠标", 89),
            make_bundle_product(5, "MetroBuds Lite 通勤降噪耳机", "蓝牙耳机", 299),
            make_bundle_product(6, "FocusLamp Mini 宿舍护眼台灯", "台灯", 199),
        ]
    )
    service = ChatService(
        intent_service=FakeIntentService(need),
        rag_pipeline=rag_pipeline,
        recommend_service=FakeRecommendService(),
        llm_client=FakeLLMClient(),
    )

    response = await service.handle_chat(ChatRequest(message="搭配一套桌面装备"), db=object())

    assert response.need_clarify is False
    assert response.structured_need == need
    assert response.bundle_plans
    assert len(response.bundle_plans) == 3
    assert response.bundle_plans[0].budget_tier == "entry"
    assert response.bundle_plans[1].budget_status in {"within_budget", "slightly_over_budget"}
    assert {item.category for item in response.bundle_plans[1].items} >= {"电脑", "显示器", "机械键盘", "鼠标", "蓝牙耳机"}
    assert response.products
    assert rag_pipeline.calls[0]["top_k"] == 30
