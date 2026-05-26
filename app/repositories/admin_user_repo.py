"""Admin user repository."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.admin_user import AdminUser


class AdminUserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_username(self, username: str) -> AdminUser | None:
        statement = select(AdminUser).where(AdminUser.username == username)
        return self.db.scalars(statement).first()

    def create_user(
        self,
        *,
        username: str,
        password_hash: str,
        email: str | None = None,
        role: str = "admin",
    ) -> AdminUser:
        user = AdminUser(username=username, email=email, password_hash=password_hash, role=role)
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return user

    def update_password(self, user: AdminUser, password_hash: str) -> AdminUser:
        user.password_hash = password_hash
        self.db.flush()
        self.db.refresh(user)
        return user
