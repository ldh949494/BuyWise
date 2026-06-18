"""Agent action audit persistence model."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AgentAction(Base):
    __tablename__ = "agent_actions"
    __table_args__ = (
        Index("ix_agent_actions_action_id", "action_id", unique=True),
        Index("ix_agent_actions_session_id", "session_id"),
        Index("ix_agent_actions_owner_subject", "owner_subject"),
        Index("ix_agent_actions_status", "status"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    action_id: Mapped[str] = mapped_column(String(64), nullable=False)
    session_id: Mapped[Optional[str]] = mapped_column(String(64))
    owner_subject: Mapped[Optional[str]] = mapped_column(String(128))
    owner_auth_type: Mapped[Optional[str]] = mapped_column(String(32))
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    confirmation_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    resolved_payload: Mapped[Optional[Any]] = mapped_column(JSON)
    result_payload: Mapped[Optional[Any]] = mapped_column(JSON)
    error_code: Mapped[Optional[str]] = mapped_column(String(64))
    request_id: Mapped[Optional[str]] = mapped_column(String(64))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
