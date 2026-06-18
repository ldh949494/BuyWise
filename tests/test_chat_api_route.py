from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import create_app
from app.models import ChatMessage, ChatSession, Product, Recommendation


KEYBOARD_CATEGORY = "\u673a\u68b0\u952e\u76d8"
QUIET_TAG = "\u4f4e\u566a\u97f3"
DORM_SCENE = "\u5bbf\u820d"
KEYBOARD_NAME = "K87 \u9759\u97f3\u7ea2\u8f74\u673a\u68b0\u952e\u76d8"
API_MESSAGE = (
    "\u63a8\u8350\u4e00\u4e2a\u5bbf\u820d\u7528\u7684"
    "\u673a\u68b0\u952e\u76d8\uff0c\u9884\u7b97300\u4ee5\u5185\uff0c"
    "\u58f0\u97f3\u5c0f\u4e00\u70b9"
)


def test_chat_api_route_is_registered_and_returns_response() -> None:
    session_factory = _session_factory_with_keyboard()
    app = create_app()

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    response = client.post(
        "/api/v1/ai/chat",
        json={"session_id": "s001", "message": API_MESSAGE},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["need_clarify"] is False
    assert payload["structured_need"]["category"] == KEYBOARD_CATEGORY
    assert payload["products"][0]["name"] == KEYBOARD_NAME
    assert KEYBOARD_NAME in payload["reply"]
    assert payload["extra"]["session_id"] == "s001"

    with session_factory() as db:
        session = db.scalar(select(ChatSession).where(ChatSession.session_id == "s001"))
        messages = list(db.scalars(select(ChatMessage).where(ChatMessage.session_id == "s001")).all())
        recommendations = list(db.scalars(select(Recommendation).where(Recommendation.session_id == "s001")).all())

    assert session is not None
    assert [message.role for message in messages] == ["user", "assistant"]
    assert recommendations
    assert recommendations[0].explanation["budget_match"] is True


def _session_factory_with_keyboard():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with session_factory() as db:
        db.add(
            Product(
                name=KEYBOARD_NAME,
                category=KEYBOARD_CATEGORY,
                price=Decimal("299.00"),
                rating=Decimal("4.8"),
                sales=1800,
                tags=[QUIET_TAG],
                suitable_scene=[DORM_SCENE],
                stock=10,
            )
        )
        db.commit()
    return session_factory
