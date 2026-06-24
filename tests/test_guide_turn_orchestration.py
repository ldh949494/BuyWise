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
                    name="CityPack 轻量通勤双肩包",
                    category="双肩包",
                    price=Decimal("239.00"),
                    tags=["轻便", "通勤"],
                    suitable_scene=["通勤", "日常使用"],
                    stock_status="in_stock",
                ),
                Product(
                    name="BudgetPack 经济双肩包",
                    category="双肩包",
                    price=Decimal("89.00"),
                    tags=["轻便"],
                    suitable_scene=["日常使用"],
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


def test_follow_up_category_change_generates_new_active_recommendation() -> None:
    client = make_client()
    session_id = "guide-turn-category-change"

    first = client.post(
        "/api/v1/ai/guide/stream",
        json={"session_id": session_id, "message": "推荐一个300以内适合宿舍的低噪音无线机械键盘"},
    )
    second = client.post(
        "/api/v1/ai/guide/follow-up/stream",
        json={"session_id": session_id, "message": "我要背包"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert '"should_refresh":true' not in second.text
    assert '"turn_type":"refresh_recommendation"' in second.text
    assert '"category":"双肩包"' in second.text
    assert "CityPack 轻量通勤双肩包" in second.text or "BudgetPack 经济双肩包" in second.text


def test_guide_stream_existing_session_uses_server_turn_orchestrator() -> None:
    client = make_client()
    session_id = "guide-turn-unified-guide-stream"

    first = client.post(
        "/api/v1/ai/guide/stream",
        json={"session_id": session_id, "message": "推荐一个300以内适合宿舍的低噪音无线机械键盘"},
    )
    second = client.post(
        "/api/v1/ai/guide/stream",
        json={"session_id": session_id, "message": "我要背包"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert '"turn_type":"refresh_recommendation"' in second.text
    assert '"category":"双肩包"' in second.text


def test_follow_up_question_keeps_snapshot_answer_path() -> None:
    client = make_client()
    session_id = "guide-turn-snapshot-question"

    client.post(
        "/api/v1/ai/guide/stream",
        json={"session_id": session_id, "message": "推荐一个300以内适合宿舍的低噪音无线机械键盘"},
    )
    response = client.post(
        "/api/v1/ai/guide/follow-up/stream",
        json={"session_id": session_id, "message": "它适用于哪些场景"},
    )

    assert response.status_code == 200
    assert '"turn_type":"answer_snapshot"' in response.text
    assert '"should_refresh":true' not in response.text
