"""Chat message persistence model."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import BigInteger, DateTime, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (Index("ix_chat_messages_session_id", "session_id"),)

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    session_id: Mapped[Optional[str]] = mapped_column(String(64))
    role: Mapped[Optional[str]] = mapped_column(String(32))
    content: Mapped[Optional[str]] = mapped_column(Text)
    structured_data: Mapped[Optional[Any]] = mapped_column(JSON)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
