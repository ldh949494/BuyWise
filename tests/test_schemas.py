from decimal import Decimal
from types import SimpleNamespace

from app.schemas.chat import ChatRequest, ChatResponse, ProductCard, StructuredNeed
from app.schemas.common import HealthResponse, ReadinessResponse
from app.schemas.compare import CompareItem, CompareRequest, CompareResponse
from app.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductRead,
    ProductUpdate,
)
from app.schemas.rag import RagItem, RagSearchRequest, RagSearchResponse


def test_chat_request_accepts_optional_multimodal_fields() -> None:
    request = ChatRequest(image_url="https://example.com/a.png")

    assert request.session_id is None
    assert request.message is None
    assert request.image_url == "https://example.com/a.png"
    assert request.audio_url is None


def test_chat_response_defaults_and_frontend_field_names() -> None:
    response = ChatResponse(reply="请补充预算", need_clarify=True)

    assert response.products == []
    assert response.extra == {}
    assert response.model_dump() == {
        "reply": "请补充预算",
        "need_clarify": True,
        "structured_need": None,
        "products": [],
        "extra": {},
    }


def test_structured_need_and_product_card_defaults() -> None:
    need = StructuredNeed(intent="recommend")
    card = ProductCard(id=1, name="Phone", price=1999)

    assert need.preferences == []
    assert need.avoid == []
    assert need.need_clarify is False
    assert need.missing_fields == []
    assert card.tags == []
    assert card.image_url is None
    assert card.rating is None
    assert card.score is None
    assert card.reason is None
    assert card.budget_match is None
    assert card.scenario_match is None
    assert card.conflicts == []
    assert card.alternatives == []


def test_product_schemas_validate_create_update_read_and_list() -> None:
    created = ProductCreate(name="Phone", price=Decimal("1999.00"), tags=["mobile"])
    updated = ProductUpdate(price=1899.0, stock=10)
    orm_product = SimpleNamespace(
        id=1,
        name="Phone",
        category="phone",
        brand="Brand",
        sku="SKU-1",
        price=Decimal("1999.00"),
        original_price=Decimal("2199.00"),
        platform="tmall",
        product_url="https://example.com/item",
        image_url="https://example.com/p.png",
        image_urls=["https://example.com/p.png", "https://example.com/p2.png"],
        rating=Decimal("4.80"),
        sales=100,
        description="good",
        specs={"memory": "8G"},
        tags=["mobile"],
        suitable_scene=["gift"],
        stock=20,
        stock_status="in_stock",
        review_summary="good reviews",
        created_at=None,
        price_history=[],
    )

    read = ProductRead.model_validate(orm_product)
    response = ProductListResponse(items=[read], total=1, page=1, page_size=20)

    assert created.name == "Phone"
    assert updated.price == 1899.0
    assert read.id == 1
    assert read.sku == "SKU-1"
    assert read.image_urls == ["https://example.com/p.png", "https://example.com/p2.png"]
    assert read.stock_status == "in_stock"
    assert read.review_summary == "good reviews"
    assert read.price == 1999.0
    assert response.items[0].name == "Phone"


def test_rag_schemas() -> None:
    request = RagSearchRequest(query="轻量无线键盘", top_k=3)
    response = RagSearchResponse(
        query=request.query,
        items=[RagItem(product_id=1, name="K87", score=0.9)],
        total=1,
    )

    assert request.query == "轻量无线键盘"
    assert request.top_k == 3
    assert response.items[0].product_id == 1
    assert response.items[0].score == 0.9


def test_compare_schemas() -> None:
    request = CompareRequest(product_ids=[1, 2], session_id="s1")
    item = CompareItem(
        id=1,
        name="Phone",
        price=1999.0,
        pros=["fast"],
        cons=["heavy"],
        score=88.5,
    )
    response = CompareResponse(items=[item], summary="更适合宿舍需求")

    assert request.product_ids == [1, 2]
    assert response.items[0].pros == ["fast"]
    assert response.summary == "更适合宿舍需求"


def test_return_models_enable_from_attributes() -> None:
    assert HealthResponse.model_config["from_attributes"] is True
    assert ReadinessResponse.model_config["from_attributes"] is True
    assert ProductRead.model_config["from_attributes"] is True
    assert ProductListResponse.model_config["from_attributes"] is True
    assert ProductCard.model_config["from_attributes"] is True
    assert StructuredNeed.model_config["from_attributes"] is True
    assert ChatResponse.model_config["from_attributes"] is True
    assert RagSearchResponse.model_config["from_attributes"] is True
    assert CompareItem.model_config["from_attributes"] is True
    assert CompareResponse.model_config["from_attributes"] is True
