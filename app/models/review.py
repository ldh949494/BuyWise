"""Review persistence model."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        Index("ix_reviews_product_id", "product_id"),
        Index("ix_reviews_order_item_id", "order_item_id"),
        Index("ix_reviews_purchase_evidence", "purchase_evidence"),
        Index("ix_reviews_source", "source"),
        Index("ix_reviews_user_ref", "user_ref"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    product_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    order_item_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    user_ref: Mapped[Optional[str]] = mapped_column(String(128))
    user_name: Mapped[Optional[str]] = mapped_column(String(64))
    rating: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))
    content: Mapped[Optional[str]] = mapped_column(Text)
    sentiment: Mapped[Optional[str]] = mapped_column(String(32))
    source: Mapped[Optional[str]] = mapped_column(String(32))
    verified_purchase: Mapped[Optional[bool]] = mapped_column(Boolean)
    purchase_evidence: Mapped[Optional[str]] = mapped_column(String(32))
    usage_context: Mapped[Optional[str]] = mapped_column(String(64))
    pros_tags: Mapped[Optional[list[str]]] = mapped_column(JSON)
    cons_tags: Mapped[Optional[list[str]]] = mapped_column(JSON)
    met_expectation: Mapped[Optional[bool]] = mapped_column(Boolean)
    status: Mapped[Optional[str]] = mapped_column(String(32))
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
