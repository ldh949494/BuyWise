"""Admin authentication service."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.providers import AppError
from app.core.transaction import unit_of_work
from app.models.admin_user import AdminUser
from app.repositories.admin_user_repo import AdminUserRepository

HASH_ALGORITHM = "pbkdf2_sha256"
PBKDF2_ITERATIONS = 210_000
MIN_PASSWORD_LENGTH = 12
DEV_DEFAULT_ADMIN_USERNAME = "admin"
DEV_DEFAULT_ADMIN_PASSWORD = "buywise-admin"


class AdminAuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AdminUserRepository(db)

    def get_authenticated_admin(self, username: str, password: str) -> AdminUser:
        user = self.repo.get_by_username(username)
        if user is None:
            return self._get_builtin_dev_admin(username, password)
        if not validate_password_hash(password, user.password_hash):
            raise AppError("Invalid username or password.", status_code=401, code="unauthorized")
        return user

    def create_access_token(self, user: AdminUser) -> tuple[str, int]:
        expires_minutes = max(settings.admin_jwt_expire_minutes, 1)
        expires_at = datetime.now(UTC) + timedelta(minutes=expires_minutes)
        payload = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "exp": int(expires_at.timestamp()),
        }
        return build_admin_token(payload), expires_minutes * 60

    def create_admin_user(
        self,
        *,
        username: str,
        password: str,
        email: str | None = None,
        reset_password: bool = False,
    ) -> AdminUser:
        validate_admin_password(password)
        password_hash = build_password_hash(password)
        user = self.repo.get_by_username(username)
        if user is None:
            user = self.repo.create_user(username=username, email=email, password_hash=password_hash)
        elif reset_password:
            user = self.repo.update_password(user, password_hash)
        else:
            raise AppError("Admin user already exists.", status_code=409, code="admin_user_exists")
        with unit_of_work(self.db) as uow:
            uow.refresh_after_commit(user)
        return user

    def _get_builtin_dev_admin(self, username: str, password: str) -> AdminUser:
        if (
            settings.app_env != "prod"
            and username == DEV_DEFAULT_ADMIN_USERNAME
            and password == DEV_DEFAULT_ADMIN_PASSWORD
        ):
            return AdminUser(id=0, username=DEV_DEFAULT_ADMIN_USERNAME, password_hash="", role="admin")
        raise AppError("Invalid username or password.", status_code=401, code="unauthorized")


def validate_admin_password(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise AppError(
            "Admin password must be at least 12 characters.",
            status_code=400,
            code="weak_admin_password",
        )


def build_password_hash(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return "$".join(
        [
            HASH_ALGORITHM,
            str(PBKDF2_ITERATIONS),
            _b64encode(salt),
            _b64encode(digest),
        ]
    )


def validate_password_hash(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, iterations_raw, salt_raw, digest_raw = encoded_hash.split("$", 3)
        if algorithm != HASH_ALGORITHM:
            return False
        iterations = int(iterations_raw)
        salt = _b64decode(salt_raw)
        expected = _b64decode(digest_raw)
    except (ValueError, TypeError):
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


def build_admin_token(payload: dict[str, Any]) -> str:
    secret = _admin_jwt_secret()
    header = {"alg": "HS256", "typ": "JWT"}
    segments = [_json_b64(header), _json_b64(payload)]
    signing_input = ".".join(segments).encode("ascii")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    segments.append(_b64encode(signature))
    return ".".join(segments)


def get_admin_token_payload(token: str) -> dict[str, Any]:
    try:
        header_raw, payload_raw, signature_raw = token.split(".", 2)
    except ValueError as exc:
        raise _invalid_token_error() from exc
    signing_input = f"{header_raw}.{payload_raw}".encode("ascii")
    expected = hmac.new(_admin_jwt_secret().encode("utf-8"), signing_input, hashlib.sha256).digest()
    try:
        supplied = _b64decode(signature_raw)
    except ValueError as exc:
        raise _invalid_token_error() from exc
    if not hmac.compare_digest(expected, supplied):
        raise _invalid_token_error()
    payload = _decode_json_segment(payload_raw)
    expires_at = payload.get("exp")
    if not isinstance(expires_at, int) or expires_at < int(datetime.now(UTC).timestamp()):
        raise _invalid_token_error()
    return payload


def _admin_jwt_secret() -> str:
    secret = settings.admin_jwt_secret.strip()
    if not secret:
        if settings.app_env == "prod":
            raise AppError("Admin JWT secret is not configured.", status_code=500, code="admin_auth_not_configured")
        return "dev-admin-jwt-secret"
    return secret


def _invalid_token_error() -> AppError:
    return AppError("Invalid admin token.", status_code=401, code="unauthorized", headers={"WWW-Authenticate": "Bearer"})


def _json_b64(value: dict[str, Any]) -> str:
    return _b64encode(json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8"))


def _decode_json_segment(segment: str) -> dict[str, Any]:
    try:
        decoded = json.loads(_b64decode(segment))
    except (ValueError, json.JSONDecodeError) as exc:
        raise _invalid_token_error() from exc
    if not isinstance(decoded, dict):
        raise _invalid_token_error()
    return decoded


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))
