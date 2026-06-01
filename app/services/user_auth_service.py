"""Ordinary user authentication service."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.transaction import unit_of_work
from app.models.user import User
from app.repositories.otp_repo import OtpRepository
from app.repositories.user_repo import UserRepository
from app.repositories.user_session_repo import UserSessionRepository
from app.services.user_token_service import (
    build_refresh_expires_at,
    build_secret_hash,
    build_user_access_token,
    generate_refresh_token,
)

OTP_PURPOSE_LOGIN = "login"
DEBUG_OTP = "123456"


@dataclass(frozen=True)
class AuthTokens:
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"


@dataclass(frozen=True)
class OtpRequestResult:
    phone_e164: str
    debug_otp: str | None = None


class UserAuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.otps = OtpRepository(db)
        self.sessions = UserSessionRepository(db)

    def create_login_otp(self, phone: str, request_ip: str | None = None) -> OtpRequestResult:
        phone_e164 = build_mainland_phone(phone)
        if settings.app_env == "prod" and not settings.auth_otp_mock_enabled:
            raise AppError("OTP provider is not configured.", status_code=503, code="otp_provider_not_configured")
        now = _utcnow()
        request_ip_hash = _hash_optional(request_ip)
        self._enforce_otp_limits(phone_e164, request_ip_hash, now)
        code = DEBUG_OTP if settings.auth_otp_mock_enabled else _random_otp()
        with unit_of_work(self.db):
            self.otps.create_challenge(
                phone_e164=phone_e164,
                code_hash=build_secret_hash(code),
                purpose=OTP_PURPOSE_LOGIN,
                expires_at=now + timedelta(minutes=max(settings.auth_otp_expire_minutes, 1)),
                request_ip_hash=request_ip_hash,
                now=now,
            )
        debug_otp = code if settings.app_env in {"dev", "test"} and settings.auth_otp_mock_enabled else None
        return OtpRequestResult(phone_e164=phone_e164, debug_otp=debug_otp)

    def validate_login_otp(
        self,
        phone: str,
        code: str,
        *,
        device_id: str | None = None,
        device_name: str | None = None,
    ) -> tuple[User, AuthTokens]:
        phone_e164 = build_mainland_phone(phone)
        now = _utcnow()
        challenge = self.otps.get_latest_active(phone_e164, OTP_PURPOSE_LOGIN, now)
        self._validate_challenge(challenge, code, now)
        user = self.users.get_by_phone(phone_e164)
        self._validate_user_can_login(user, challenge, now)
        return self._complete_otp_login(user, phone_e164, challenge, now, device_id, device_name)

    def create_refreshed_tokens(self, refresh_token: str) -> AuthTokens:
        now = _utcnow()
        session = self.sessions.get_by_refresh_token_hash(build_secret_hash(refresh_token))
        user = self._validate_refresh_session(session, now)
        new_refresh = generate_refresh_token()
        access_token, expires_in = build_user_access_token(user.id, now=now)
        with unit_of_work(self.db):
            self._replace_refresh_session(session, user.id, new_refresh, now)
            self.users.update_logged_in(user, now)
        return AuthTokens(access_token=access_token, refresh_token=new_refresh, expires_in=expires_in)

    def update_logout(self, refresh_token: str) -> None:
        session = self.sessions.get_by_refresh_token_hash(build_secret_hash(refresh_token))
        if session is None:
            return
        with unit_of_work(self.db):
            self.sessions.update_revoked(session, _utcnow())

    def get_user_by_subject(self, subject: str) -> User | None:
        if not subject.startswith("user:"):
            return None
        try:
            user_id = int(subject.split(":", 1)[1])
        except ValueError:
            return None
        return self.users.get_by_id(user_id)

    def _validate_challenge(self, challenge, code: str, now: datetime) -> None:
        if challenge is None:
            raise AppError("Invalid or expired verification code.", status_code=401, code="invalid_otp")
        if challenge.attempt_count >= settings.auth_otp_max_attempts:
            challenge.consumed_at = now
            with unit_of_work(self.db):
                self.db.add(challenge)
            raise AppError("Invalid or expired verification code.", status_code=401, code="invalid_otp")
        challenge.attempt_count += 1
        if not hmac.compare_digest(challenge.code_hash, build_secret_hash(code.strip())):
            with unit_of_work(self.db):
                self.db.add(challenge)
            raise AppError("Invalid or expired verification code.", status_code=401, code="invalid_otp")

    def _validate_user_can_login(self, user: User | None, challenge, now: datetime) -> None:
        if user is not None and user.status == "disabled":
            challenge.consumed_at = now
            with unit_of_work(self.db):
                self.db.add(challenge)
            raise AppError("Account is disabled.", status_code=403, code="account_disabled")

    def _complete_otp_login(
        self,
        user: User | None,
        phone_e164: str,
        challenge,
        now: datetime,
        device_id: str | None,
        device_name: str | None,
    ) -> tuple[User, AuthTokens]:
        with unit_of_work(self.db) as uow:
            challenge.consumed_at = now
            self.db.add(challenge)
            user = user or self.users.create_user(phone_e164, now)
            self.users.update_logged_in(user, now)
            tokens = self._create_session_tokens(user.id, now, device_id=device_id, device_name=device_name)
            uow.refresh_after_commit(user)
        return user, tokens

    def _validate_refresh_session(self, session, now: datetime) -> User:
        if session is None:
            raise AppError("Invalid refresh token.", status_code=401, code="unauthorized")
        if session.revoked_at is not None:
            with unit_of_work(self.db):
                self.sessions.update_all_revoked_for_user(session.user_id, now)
            raise AppError("Invalid refresh token.", status_code=401, code="unauthorized")
        if session.expires_at < now:
            with unit_of_work(self.db):
                self.sessions.update_revoked(session, now)
            raise AppError("Invalid refresh token.", status_code=401, code="unauthorized")
        user = self.users.get_by_id(session.user_id)
        if user is None or user.status == "disabled":
            with unit_of_work(self.db):
                self.sessions.update_revoked(session, now)
            code = "account_disabled" if user is not None else "unauthorized"
            status_code = 403 if user is not None else 401
            raise AppError("Account is disabled.", status_code=status_code, code=code)
        return user

    def _replace_refresh_session(self, session, user_id: int, refresh_token: str, now: datetime) -> None:
        self.sessions.update_revoked(session, now)
        session.rotated_at = now
        self.sessions.create_session(
            user_id=user_id,
            refresh_token_hash=build_secret_hash(refresh_token),
            expires_at=build_refresh_expires_at(now),
            now=now,
            device_id=session.device_id,
            device_name=session.device_name,
        )

    def _create_session_tokens(
        self,
        user_id: int,
        now: datetime,
        *,
        device_id: str | None,
        device_name: str | None,
    ) -> AuthTokens:
        access_token, expires_in = build_user_access_token(user_id, now=now)
        refresh_token = generate_refresh_token()
        self.sessions.create_session(
            user_id=user_id,
            refresh_token_hash=build_secret_hash(refresh_token),
            expires_at=build_refresh_expires_at(now),
            now=now,
            device_id=device_id,
            device_name=device_name,
        )
        return AuthTokens(access_token=access_token, refresh_token=refresh_token, expires_in=expires_in)

    def _enforce_otp_limits(self, phone_e164: str, request_ip_hash: str | None, now: datetime) -> None:
        latest = self.otps.get_phone_count_since(phone_e164, now - timedelta(seconds=settings.auth_otp_cooldown_seconds))
        if latest > 0:
            raise AppError("Verification code was requested too recently.", status_code=429, code="otp_rate_limited")
        if self.otps.get_phone_count_since(phone_e164, now - timedelta(hours=1)) >= settings.auth_otp_phone_hour_limit:
            raise AppError("Too many verification code requests.", status_code=429, code="otp_rate_limited")
        if self.otps.get_phone_count_since(phone_e164, now - timedelta(days=1)) >= settings.auth_otp_phone_day_limit:
            raise AppError("Too many verification code requests.", status_code=429, code="otp_rate_limited")
        if request_ip_hash is not None:
            if self.otps.get_ip_count_since(request_ip_hash, now - timedelta(minutes=1)) >= settings.auth_otp_ip_minute_limit:
                raise AppError("Too many verification code requests.", status_code=429, code="otp_rate_limited")
            if self.otps.get_ip_count_since(request_ip_hash, now - timedelta(hours=1)) >= settings.auth_otp_ip_hour_limit:
                raise AppError("Too many verification code requests.", status_code=429, code="otp_rate_limited")


def build_mainland_phone(phone: str) -> str:
    value = phone.strip().replace(" ", "").replace("-", "")
    if value.startswith("+86"):
        national = value[3:]
    else:
        national = value
    if len(national) != 11 or not national.startswith("1") or not national.isdigit():
        raise AppError("Invalid phone number.", status_code=400, code="invalid_phone_number")
    return f"+86{national}"


def build_masked_phone(phone_e164: str) -> str:
    if phone_e164.startswith("+86") and len(phone_e164) == 14:
        return f"+86{phone_e164[3:6]}****{phone_e164[-4:]}"
    return phone_e164[:3] + "****" + phone_e164[-4:]


def _random_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _hash_optional(value: str | None) -> str | None:
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)
