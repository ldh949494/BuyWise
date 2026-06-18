"""Chat repository."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.recommendation import Recommendation


class ChatRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_session(self, session_id: str | None) -> ChatSession | None:
        normalized_session_id = (session_id or "").strip()
        if not normalized_session_id:
            return None
        return self.db.scalar(select(ChatSession).where(ChatSession.session_id == normalized_session_id))

    def create_session(
        self,
        *,
        session_id: str | None = None,
        title: str | None = None,
        owner_subject: str | None = None,
        owner_auth_type: str | None = None,
        user_id: int | None = None,
        session_token_hash: str | None = None,
        expires_at: datetime | None = None,
    ) -> ChatSession:
        now = datetime.utcnow()
        session = ChatSession(
            session_id=(session_id or "").strip() or self.generate_session_id(),
            user_id=user_id,
            owner_subject=owner_subject,
            owner_auth_type=owner_auth_type,
            session_token_hash=session_token_hash,
            expires_at=expires_at,
            title=title,
            created_at=now,
            updated_at=now,
        )
        self.db.add(session)
        self.db.flush()
        return session

    def get_or_create_session(self, session_id: str | None = None, title: str | None = None) -> ChatSession:
        session = self.get_session(session_id)
        if session is not None:
            return session
        return self.create_session(session_id=session_id, title=title)

    def update_session_activity(self, session: ChatSession, expires_at: datetime | None) -> None:
        session.updated_at = datetime.utcnow()
        session.expires_at = expires_at
        self.db.flush()

    def create_message(
        self,
        session_id: str,
        role: str,
        content: str | None,
        structured_data: dict[str, Any] | None = None,
    ) -> ChatMessage:
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            structured_data=structured_data,
            created_at=datetime.utcnow(),
        )
        self.db.add(message)
        self.db.flush()
        return message

    def create_recommendations(
        self,
        session_id: str,
        products: list[Any],
    ) -> list[Recommendation]:
        records = []
        for product in products:
            record = Recommendation(
                session_id=session_id,
                product_id=self._get_value(product, "id"),
                reason=self._get_value(product, "reason"),
                score=self._get_value(product, "score"),
                explanation={
                    "budget_match": self._get_value(product, "budget_match"),
                    "scenario_match": self._get_value(product, "scenario_match"),
                    "conflicts": self._get_value(product, "conflicts") or [],
                    "alternatives": self._get_value(product, "alternatives") or [],
                },
                created_at=datetime.utcnow(),
            )
            self.db.add(record)
            records.append(record)
        self.db.flush()
        return records

    def list_messages(self, session_id: str, limit: int = 20) -> list[ChatMessage]:
        statement = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
            .limit(limit)
        )
        return list(reversed(self.db.scalars(statement).all()))

    def generate_session_id(self) -> str:
        return uuid.uuid4().hex

    def _get_value(self, source: Any, key: str) -> Any:
        if isinstance(source, dict):
            return source.get(key)
        return getattr(source, key, None)
