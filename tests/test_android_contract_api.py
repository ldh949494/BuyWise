from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.compare import get_compare_service
from app.core.database import Base, get_db
from app.main import create_app
from app.scripts.seed_products import seed_android_contract_products
from app.services.compare_service import CompareService


KEYBOARD_ID = 1001
SECOND_KEYBOARD_ID = 1002
KEYBOARD_NAME = "K87 静音红轴机械键盘"
KEYBOARD_CATEGORY = "机械键盘"
CHAT_SESSION_ID = "android-contract-session"
CHAT_MESSAGE = "推荐一个宿舍写代码用的机械键盘，预算300以内，声音小一点"


class FakeCompareLLMClient:
    async def generate_compare_summary(self, user_need, products):
        return f"Android contract compare summary: {products[0].name}"


def make_android_contract_client() -> TestClient:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with session_factory() as db:
        seed_android_contract_products(db)

    app = create_app()

    def override_get_db() -> Iterator[Session]:
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_compare_service] = lambda: CompareService(
        llm_client=FakeCompareLLMClient()
    )
    return TestClient(app)


def test_android_product_browse_contract_returns_list_and_detail_payloads() -> None:
    client = make_android_contract_client()

    list_response = client.get(
        "/api/v1/products",
        params={"category": KEYBOARD_CATEGORY, "page": 1, "page_size": 10},
    )

    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["page"] == 1
    assert list_payload["page_size"] == 10
    assert list_payload["total"] == 2
    assert [item["id"] for item in list_payload["items"]] == [KEYBOARD_ID, SECOND_KEYBOARD_ID]

    first_item = list_payload["items"][0]
    assert first_item["name"] == KEYBOARD_NAME
    assert first_item["brand"] == "KeyNova"
    assert first_item["sku"] == "android-keyboard-k87"
    assert first_item["price"] == 269.0
    assert first_item["rating"] == 4.8
    assert first_item["image_url"].startswith("https://")
    assert first_item["stock_status"] == "in_stock"
    assert "静音" in first_item["tags"]
    assert "宿舍" in first_item["suitable_scene"]

    detail_response = client.get(f"/api/v1/products/{KEYBOARD_ID}")

    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["id"] == KEYBOARD_ID
    assert detail_payload["name"] == KEYBOARD_NAME
    assert detail_payload["product_url"].startswith("https://")
    assert detail_payload["specs"]["switch"] == "静音红轴"
    assert detail_payload["review_summary"]


def test_android_product_compare_contract_returns_frontend_ready_shape() -> None:
    client = make_android_contract_client()

    response = client.post(
        "/api/v1/products/compare",
        json={
            "product_ids": [KEYBOARD_ID, SECOND_KEYBOARD_ID],
            "user_need": "宿舍使用，安静，预算300以内",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["winner_id"] == KEYBOARD_ID
    assert KEYBOARD_NAME in payload["summary"]
    assert [item["product_id"] for item in payload["items"]] == [KEYBOARD_ID, SECOND_KEYBOARD_ID]

    winner = payload["items"][0]
    assert winner["id"] == KEYBOARD_ID
    assert winner["name"] == KEYBOARD_NAME
    assert winner["price"] == 269.0
    assert winner["rating"] == 4.8
    assert winner["score"] > payload["items"][1]["score"]
    assert "安静" in winner["pros"]
    assert "价格合适" in winner["pros"]
    assert "适合宿舍" in winner["pros"]
    assert "不支持无线" in winner["cons"]
    assert winner["specs"]["layout"] == "87键"


def test_android_ai_guide_contract_returns_structured_need_products_and_session() -> None:
    client = make_android_contract_client()

    response = client.post(
        "/api/v1/ai/chat",
        json={"session_id": CHAT_SESSION_ID, "message": CHAT_MESSAGE},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["need_clarify"] is False
    assert payload["extra"]["session_id"] == CHAT_SESSION_ID
    assert KEYBOARD_NAME in payload["reply"]

    structured_need = payload["structured_need"]
    assert structured_need["intent"] == "商品推荐"
    assert structured_need["category"] == KEYBOARD_CATEGORY
    assert structured_need["budget_max"] == 300
    assert structured_need["scenario"] == "宿舍"
    assert "低噪音" in structured_need["preferences"]

    products = payload["products"]
    assert products
    assert products[0]["id"] == KEYBOARD_ID
    assert products[0]["name"] == KEYBOARD_NAME
    assert products[0]["price"] == 269.0
    assert products[0]["budget_match"] is True
    assert products[0]["scenario_match"] is True
    assert products[0]["reason"]
    assert isinstance(products[0]["conflicts"], list)
    assert isinstance(products[0]["alternatives"], list)
