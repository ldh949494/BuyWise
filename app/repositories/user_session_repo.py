"""Repository for user refresh-token sessions."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user_session import UserSession


class UserSessionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_refresh_token_hash(self, token_hash: str) -> UserSession | None:
        statement = select(UserSession).where(UserSession.refresh_token_hash == token_hash)
        return self.db.scalar(statement)

    def create_session(
        self,
        *,
        user_id: int,
        refresh_token_hash: str,
        expires_at: datetime,
        now: datetime,
        device_id: str | None = None,
        device_name: str | None = None,
    ) -> UserSession:
        session = UserSession(
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
            device_id=device_id,
            device_name=device_name,
            created_at=now,
            last_used_at=now,
            expires_at=expires_at,
        )
        self.db.add(session)
        self.db.flush()
        return session

    def update_revoked(self, session: UserSession, now: datetime) -> UserSession:
        session.revoked_at = session.revoked_at or now
        session.last_used_at = now
        self.db.add(session)
        return session

    def update_rotated(self, session: UserSession, refresh_token_hash: str, expires_at: datetime, now: datetime) -> UserSession:
        session.refresh_token_hash = refresh_token_hash
        session.rotated_at = now
        session.revoked_at = None
        session.expires_at = expires_at
        session.last_used_at = now
        self.db.add(session)
        return session

    def update_all_revoked_for_user(self, user_id: int, now: datetime) -> None:
        sessions = self.db.scalars(
            select(UserSession).where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
        ).all()
        for session in sessions:
            session.revoked_at = now
            session.last_used_at = now
            self.db.add(session)
