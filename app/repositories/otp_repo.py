"""Repository for OTP challenges."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.otp_challenge import OtpChallenge


class OtpRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_challenge(
        self,
        *,
        phone_e164: str,
        code_hash: str,
        purpose: str,
        expires_at: datetime,
        request_ip_hash: str | None,
        now: datetime,
    ) -> OtpChallenge:
        challenge = OtpChallenge(
            phone_e164=phone_e164,
            code_hash=code_hash,
            purpose=purpose,
            expires_at=expires_at,
            request_ip_hash=request_ip_hash,
            created_at=now,
        )
        self.db.add(challenge)
        self.db.flush()
        return challenge

    def get_latest_active(self, phone_e164: str, purpose: str, now: datetime) -> OtpChallenge | None:
        statement = (
            select(OtpChallenge)
            .where(
                OtpChallenge.phone_e164 == phone_e164,
                OtpChallenge.purpose == purpose,
                OtpChallenge.consumed_at.is_(None),
                OtpChallenge.expires_at >= now,
            )
            .order_by(OtpChallenge.created_at.desc(), OtpChallenge.id.desc())
        )
        return self.db.scalar(statement)

    def get_phone_count_since(self, phone_e164: str, since: datetime) -> int:
        statement = select(func.count()).select_from(OtpChallenge).where(
            OtpChallenge.phone_e164 == phone_e164,
            OtpChallenge.created_at >= since,
        )
        return int(self.db.scalar(statement) or 0)

    def get_ip_count_since(self, request_ip_hash: str, since: datetime) -> int:
        statement = select(func.count()).select_from(OtpChallenge).where(
            OtpChallenge.request_ip_hash == request_ip_hash,
            OtpChallenge.created_at >= since,
        )
        return int(self.db.scalar(statement) or 0)
