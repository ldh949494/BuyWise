"""Review persistence model."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (Index("ix_reviews_product_id", "product_id"),)

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    product_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    user_name: Mapped[Optional[str]] = mapped_column(String(64))
    rating: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))
    content: Mapped[Optional[str]] = mapped_column(Text)
    sentiment: Mapped[Optional[str]] = mapped_column(String(32))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
