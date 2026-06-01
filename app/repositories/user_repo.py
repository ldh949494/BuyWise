"""Repository for ordinary users."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_phone(self, phone_e164: str) -> User | None:
        statement = select(User).where(User.phone_e164 == phone_e164)
        return self.db.scalar(statement)

    def create_user(self, phone_e164: str, now: datetime) -> User:
        user = User(
            phone_e164=phone_e164,
            display_name=f"BuyWise 用户 {phone_e164[-4:]}",
            status="active",
            phone_verified_at=now,
            last_login_at=now,
            created_at=now,
            updated_at=now,
        )
        self.db.add(user)
        self.db.flush()
        return user

    def update_logged_in(self, user: User, now: datetime) -> User:
        user.phone_verified_at = user.phone_verified_at or now
        user.last_login_at = now
        user.updated_at = now
        self.db.add(user)
        return user
