from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import create_app
from app.scripts.seed_products import seed_demo_products


DEMO_QUESTION = "帮我推荐一个300以内适合宿舍写代码的低噪音无线机械键盘，最好性价比高"
BUNDLE_QUESTION = "下周去旅行，帮我搭配一套轻便出行清单，预算700以内，不要大容量"


def make_demo_client() -> TestClient:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with session_factory() as db:
        seed_demo_products(db)

    app = create_app()

    def override_get_db() -> Iterator[Session]:
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_demo_showcase_question_returns_wireless_quiet_keyboard_first() -> None:
    client = make_demo_client()

    response = client.post(
        "/api/v1/ai/chat",
        json={"session_id": "demo-showcase-session", "message": DEMO_QUESTION},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["need_clarify"] is False

    structured_need = payload["structured_need"]
    assert structured_need["category"] == "机械键盘"
    assert structured_need["budget_max"] == 300
    assert structured_need["scenario"] == "宿舍"
    assert "低噪音" in structured_need["preferences"]
    assert "无线" in structured_need["preferences"]

    products = payload["products"]
    assert products[0]["id"] == 1101
    assert products[0]["name"] == "Campus75 三模静音机械键盘"
    assert products[0]["budget_match"] is True
    assert products[0]["scenario_match"] is True
    assert "符合无线偏好" in products[0]["reason"]


def test_demo_bundle_question_returns_cross_category_plan_within_budget() -> None:
    client = make_demo_client()

    response = client.post(
        "/api/v1/ai/chat",
        json={"session_id": "demo-bundle-session", "message": BUNDLE_QUESTION},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["need_clarify"] is False
    assert payload["structured_need"]["intent"] == "场景化组合推荐"
    assert payload["structured_need"]["scenario"] == "旅行"
    assert "大容量" in payload["structured_need"]["avoid"]

    products = payload["products"]
    names = {product["name"] for product in products}
    assert len(products) >= 2
    assert sum(product["price"] for product in products) <= 700
    assert "TravelGo 10000mAh 轻薄充电宝" in names
    assert "CityPack 轻量通勤双肩包" in names
