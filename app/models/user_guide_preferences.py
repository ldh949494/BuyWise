"""User guide preferences persistence model."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Index, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserGuidePreferences(Base):
    __tablename__ = "user_guide_preferences"
    __table_args__ = (Index("ix_user_guide_preferences_user_id", "user_id", unique=True),)

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    budget_policy: Mapped[str] = mapped_column(String(32), nullable=False, default="slightly_flexible")
    presentation_style: Mapped[str] = mapped_column(String(32), nullable=False, default="compare_options")
    preferences_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
