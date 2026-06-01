"""Token helpers for ordinary user authentication."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.config import settings
from app.utils.jwt import build_hs256_jwt, decode_hs256_jwt


class UserTokenError(Exception):
    """User JWT decode or signing error."""

USER_SCOPES = (
    "orders:read",
    "orders:write",
    "feedback:read",
    "feedback:write",
    "upload:write",
)


def build_user_access_token(user_id: int, *, now: datetime | None = None) -> tuple[str, int]:
    issued_at = _as_utc(now or datetime.now(UTC))
    expires_minutes = max(settings.user_jwt_expire_minutes, 1)
    expires_at = issued_at + timedelta(minutes=expires_minutes)
    payload = {
        "sub": f"user:{user_id}",
        "typ": "access",
        "auth_type": "user",
        "jti": secrets.token_urlsafe(16),
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return build_user_token(payload), expires_minutes * 60


def build_user_token(payload: dict[str, Any]) -> str:
    return build_hs256_jwt(payload, _user_jwt_secret())


def get_user_token_payload(token: str) -> dict[str, Any]:
    payload = decode_hs256_jwt(token, _user_jwt_secret(), _invalid_token_error)
    if payload.get("typ") != "access" or payload.get("auth_type") != "user":
        raise _invalid_token_error()
    expires_at = payload.get("exp")
    if not isinstance(expires_at, int) or expires_at < int(datetime.now(UTC).timestamp()):
        raise _invalid_token_error()
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.startswith("user:"):
        raise _invalid_token_error()
    return payload


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def build_secret_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_refresh_expires_at(now: datetime) -> datetime:
    return now + timedelta(days=max(settings.user_refresh_token_expire_days, 1))


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _user_jwt_secret() -> str:
    secret = settings.user_jwt_secret.strip()
    if not secret:
        if settings.app_env == "prod":
            raise UserTokenError("user_auth_not_configured")
        return "dev-user-jwt-secret"
    return secret


def _invalid_token_error() -> UserTokenError:
    return UserTokenError("invalid_user_token")
