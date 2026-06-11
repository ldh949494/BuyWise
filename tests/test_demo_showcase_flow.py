from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.dependencies import AppContainerBuilder
from app.core.database import Base, get_db
from app.main import create_app
from app.scripts.seed_products import seed_demo_products


DEMO_QUESTION = "帮我推荐一个300以内适合宿舍写代码的低噪音无线机械键盘，最好性价比高"
BUNDLE_QUESTION = "帮我配齐一套6000元以内的桌面装备，包括电脑、显示器、键盘、鼠标和耳机"
BROAD_TARGET_CASES = [
    ("租房做饭用的空气炸锅", 1301, "空气炸锅"),
    ("想看吸尘器", 1303, "吸尘器"),
    ("卧室投影仪", 1305, "投影仪"),
]


class EmptyProductStore:
    def search(self, query: str, top_k: int = 10) -> list[dict]:
        return []

    def count(self) -> int:
        return 0

    def indexed_product_ids(self) -> list[int]:
        return []


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

    app = create_app(AppContainerBuilder().with_product_store(EmptyProductStore()))

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
    assert payload["structured_need"]["intent"] == "bundle_recommend"
    assert payload["structured_need"]["scenario"] == "桌面"

    plans = payload["bundle_plans"]
    assert len(plans) == 3
    assert [plan["budget_tier"] for plan in plans] == ["entry", "balanced", "premium"]
    balanced = plans[1]
    categories = {item["category"] for item in balanced["items"]}
    assert {"电脑", "显示器", "机械键盘", "鼠标", "蓝牙耳机"}.issubset(categories)
    assert balanced["budget_status"] in {"within_budget", "slightly_over_budget"}
    assert balanced["completeness"]["included_required"] >= 5


def test_demo_broad_target_questions_return_relevant_products() -> None:
    client = make_demo_client()

    for message, product_id, category in BROAD_TARGET_CASES:
        response = client.post("/api/v1/ai/chat", json={"session_id": f"demo-{product_id}", "message": message})

        assert response.status_code == 200
        payload = response.json()
        assert payload["need_clarify"] is False
        assert payload["structured_need"]["category"] == category
        assert payload["products"][0]["id"] == product_id
        assert payload["extra"]["result_quality"] == "exact"


def test_demo_broad_empty_question_returns_low_confidence_products() -> None:
    client = make_demo_client()

    response = client.post("/api/v1/ai/chat", json={"session_id": "demo-broad-empty", "message": "推荐一下"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["need_clarify"] is False
    assert payload["products"]
    assert payload["extra"]["fallback_stage"] == "fallback_popular"
    assert payload["extra"]["result_quality"] == "low_confidence"


def test_demo_guide_stream_emits_broad_target_and_low_confidence_states() -> None:
    client = make_demo_client()

    target_response = client.post(
        "/api/v1/ai/guide/stream",
        json={"session_id": "guide-broad-air-fryer", "message": "租房做饭用的空气炸锅"},
    )
    broad_response = client.post(
        "/api/v1/ai/guide/stream",
        json={"session_id": "guide-broad-empty", "message": "推荐一下"},
    )

    assert target_response.status_code == 200
    assert '"id":1301' in target_response.text
    assert '"need_clarify":false' in target_response.text
    assert '"result_quality":"exact"' in target_response.text
    assert broad_response.status_code == 200
    assert '"fallback_stage":"fallback_popular"' in broad_response.text
    assert '"result_quality":"low_confidence"' in broad_response.text
