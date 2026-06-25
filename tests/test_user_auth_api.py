from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import create_app
from app.models import OtpChallenge, User, UserSession
from app.services.user_token_service import get_user_token_payload


def make_client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    app = create_app()

    def override_get_db():
        session = testing_session_local()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), testing_session_local


def test_otp_request_returns_debug_code_and_hashes_stored_code() -> None:
    client, session_factory = make_client()

    response = client.post("/api/v1/auth/otp/request", json={"phone": "13812345678"})

    assert response.status_code == 200
    assert response.json() == {"phone_masked": "+86138****5678", "debug_otp": "123456"}
    with session_factory() as db:
        challenge = db.query(OtpChallenge).one()
        assert challenge.phone_e164 == "+8613812345678"
        assert challenge.code_hash != "123456"


def test_otp_request_rejects_invalid_phone_and_rate_limits() -> None:
    client, _ = make_client()

    invalid = client.post("/api/v1/auth/otp/request", json={"phone": "123"})
    blank = client.post("/api/v1/auth/otp/request", json={"phone": ""})
    first = client.post("/api/v1/auth/otp/request", json={"phone": "13812345678"})
    second = client.post("/api/v1/auth/otp/request", json={"phone": "13812345678"})

    assert invalid.status_code == 400
    assert invalid.json()["code"] == "invalid_phone_number"
    assert blank.status_code == 400
    assert blank.json()["code"] == "invalid_phone_number"
    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["code"] == "otp_rate_limited"


def test_verify_otp_auto_creates_user_and_tokens_without_phone_claim() -> None:
    client, session_factory = make_client()
    client.post("/api/v1/auth/otp/request", json={"phone": "+8613812345678"})

    response = client.post(
        "/api/v1/auth/otp/verify",
        json={"phone": "13812345678", "code": "123456", "device_name": "Pixel"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["refresh_token"]
    assert payload["user"]["phone_masked"] == "+86138****5678"
    claims = get_user_token_payload(payload["access_token"])
    assert claims["sub"].startswith("user:")
    assert claims["auth_type"] == "user"
    assert "phone" not in claims
    with session_factory() as db:
        user = db.query(User).one()
        session = db.query(UserSession).one()
        assert user.phone_e164 == "+8613812345678"
        assert session.refresh_token_hash != payload["refresh_token"]
        assert session.device_name == "Pixel"


def test_verify_otp_rejects_wrong_and_expired_codes() -> None:
    client, session_factory = make_client()
    client.post("/api/v1/auth/otp/request", json={"phone": "13812345678"})

    blank_code = client.post("/api/v1/auth/otp/verify", json={"phone": "13812345678", "code": ""})
    wrong = client.post("/api/v1/auth/otp/verify", json={"phone": "13812345678", "code": "000000"})
    with session_factory() as db:
        challenge = db.query(OtpChallenge).one()
        challenge.expires_at = datetime.utcnow() - timedelta(minutes=1)
        db.commit()
    expired = client.post("/api/v1/auth/otp/verify", json={"phone": "13812345678", "code": "123456"})

    assert blank_code.status_code == 401
    assert blank_code.json()["code"] == "invalid_otp"
    assert wrong.status_code == 401
    assert wrong.json()["code"] == "invalid_otp"
    assert expired.status_code == 401
    assert expired.json()["code"] == "invalid_otp"


def test_refresh_rotates_token_and_replay_revokes_current_session() -> None:
    client, session_factory = make_client()
    client.post("/api/v1/auth/otp/request", json={"phone": "13812345678"})
    login = client.post("/api/v1/auth/otp/verify", json={"phone": "13812345678", "code": "123456"}).json()

    refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]})
    replay = client.post("/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]})
    current = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh.json()["refresh_token"]})

    assert refresh.status_code == 200
    assert refresh.json()["refresh_token"] != login["refresh_token"]
    assert replay.status_code == 401
    assert current.status_code == 401
    with session_factory() as db:
        assert db.query(UserSession).filter(UserSession.revoked_at.is_(None)).count() == 0


def test_logout_revokes_refresh_token_and_me_returns_masked_user() -> None:
    client, session_factory = make_client()
    client.post("/api/v1/auth/otp/request", json={"phone": "13812345678"})
    login = client.post("/api/v1/auth/otp/verify", json={"phone": "13812345678", "code": "123456"}).json()

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {login['access_token']}"})
    logout = client.post("/api/v1/auth/logout", json={"refresh_token": login["refresh_token"]})
    refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]})

    assert me.status_code == 200
    assert me.json()["phone_masked"] == "+86138****5678"
    assert logout.status_code == 204
    assert refresh.status_code == 401
    with session_factory() as db:
        assert db.query(UserSession).one().revoked_at is not None


def test_disabled_user_cannot_login_or_refresh() -> None:
    client, session_factory = make_client()
    client.post("/api/v1/auth/otp/request", json={"phone": "13812345678"})
    login = client.post("/api/v1/auth/otp/verify", json={"phone": "13812345678", "code": "123456"}).json()
    with session_factory() as db:
        user = db.query(User).one()
        user.status = "disabled"
        db.commit()
    settings.auth_otp_cooldown_seconds = 0
    client.post("/api/v1/auth/otp/request", json={"phone": "13812345678"})

    disabled_login = client.post("/api/v1/auth/otp/verify", json={"phone": "13812345678", "code": "123456"})
    disabled_refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]})

    assert disabled_login.status_code == 403
    assert disabled_login.json()["code"] == "account_disabled"
    assert disabled_refresh.status_code == 403
    assert disabled_refresh.json()["code"] == "account_disabled"


def test_user_jwt_has_user_scopes_but_not_product_write() -> None:
    client, _ = make_client()
    client.post("/api/v1/auth/otp/request", json={"phone": "13812345678"})
    login = client.post("/api/v1/auth/otp/verify", json={"phone": "13812345678", "code": "123456"}).json()
    headers = {"Authorization": f"Bearer {login['access_token']}"}

    orders = client.get("/api/v1/orders", headers=headers)
    product_write = client.post("/api/v1/products", json={"name": "Tablet"}, headers=headers)
    admin = client.get("/api/v1/admin/ops/summary", headers=headers)

    assert orders.status_code == 200
    assert product_write.status_code == 403
    assert admin.status_code == 401
