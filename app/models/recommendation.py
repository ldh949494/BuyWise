"""Recommendation persistence model."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from typing import Any

from sqlalchemy import BigInteger, DateTime, Index, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"
    __table_args__ = (
        Index("ix_recommendations_session_id", "session_id"),
        Index("ix_recommendations_product_id", "product_id"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    session_id: Mapped[Optional[str]] = mapped_column(String(64))
    product_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    explanation: Mapped[Optional[Any]] = mapped_column(JSON)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
