from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import create_app
from app.models import Product


def make_client() -> TestClient:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with session_factory() as db:
        db.add_all(
            [
                Product(
                    name="Campus75 三模静音机械键盘",
                    category="机械键盘",
                    price=Decimal("299.00"),
                    tags=["低噪音", "无线"],
                    suitable_scene=["宿舍"],
                    stock_status="in_stock",
                ),
                Product(
                    name="Office68 轻薄无线机械键盘",
                    category="机械键盘",
                    price=Decimal("259.00"),
                    tags=["无线", "轻薄"],
                    suitable_scene=["办公"],
                    stock_status="in_stock",
                ),
                Product(
                    name="FocusK Pro 有线静音机械键盘",
                    category="机械键盘",
                    price=Decimal("459.00"),
                    tags=["低噪音", "有线"],
                    suitable_scene=["宿舍", "办公"],
                    stock_status="in_stock",
                ),
            ]
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
    return TestClient(app)


def test_chat_multiturn_budget_update_reuses_prior_context_and_reranks() -> None:
    client = make_client()
    session_id = "multiturn-budget"

    first = client.post(
        "/api/v1/ai/chat",
        json={"session_id": session_id, "message": "推荐一个300以内适合宿舍的低噪音无线机械键盘"},
    )
    second = client.post(
        "/api/v1/ai/chat",
        json={"session_id": session_id, "message": "预算改到500"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    need = second.json()["structured_need"]
    assert need["category"] == "机械键盘"
    assert need["budget_max"] == 500
    assert need["scenario"] == "宿舍"
    assert set(need["preferences"]) == {"低噪音", "无线"}
    assert second.json()["products"]


def test_chat_multiturn_scenario_update_overrides_prior_scene() -> None:
    client = make_client()
    session_id = "multiturn-scenario"

    client.post(
        "/api/v1/ai/chat",
        json={"session_id": session_id, "message": "推荐一个300以内适合宿舍的低噪音无线机械键盘"},
    )
    second = client.post(
        "/api/v1/ai/chat",
        json={"session_id": session_id, "message": "换成办公用"},
    )

    assert second.status_code == 200
    need = second.json()["structured_need"]
    assert need["category"] == "机械键盘"
    assert need["budget_max"] == 300
    assert need["scenario"] == "办公"
    assert set(need["preferences"]) == {"低噪音", "无线"}


def test_chat_multiturn_negative_preference_does_not_keep_conflicting_preference() -> None:
    client = make_client()
    session_id = "multiturn-negative-preference"

    client.post(
        "/api/v1/ai/chat",
        json={"session_id": session_id, "message": "推荐一个500以内适合宿舍的低噪音无线机械键盘"},
    )
    second = client.post(
        "/api/v1/ai/chat",
        json={"session_id": session_id, "message": "不要无线"},
    )

    assert second.status_code == 200
    need = second.json()["structured_need"]
    assert need["category"] == "机械键盘"
    assert need["budget_max"] == 500
    assert need["scenario"] == "宿舍"
    assert need["preferences"] == ["低噪音"]
    assert need["avoid"] == ["无线"]


def test_chat_multiturn_replacement_preference_drops_replaced_prior_preference() -> None:
    client = make_client()
    session_id = "multiturn-replace-preference"

    client.post(
        "/api/v1/ai/chat",
        json={"session_id": session_id, "message": "推荐一个500以内适合宿舍的低噪音无线机械键盘"},
    )
    second = client.post(
        "/api/v1/ai/chat",
        json={"session_id": session_id, "message": "换成有线"},
    )

    assert second.status_code == 200
    need = second.json()["structured_need"]
    assert need["category"] == "机械键盘"
    assert need["budget_max"] == 500
    assert need["scenario"] == "宿舍"
    assert need["preferences"] == ["有线"]
    assert second.json()["products"][0]["name"] == "FocusK Pro 有线静音机械键盘"
