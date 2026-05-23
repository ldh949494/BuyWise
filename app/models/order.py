"""Order persistence models for the simulated purchase loop."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (Index("ix_orders_user_ref", "user_ref"),)

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    user_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    payment_status: Mapped[str] = mapped_column(String(32), nullable=False)
    fulfillment_status: Mapped[str] = mapped_column(String(32), nullable=False)
    external_platform: Mapped[Optional[str]] = mapped_column(String(64))
    external_order_ref: Mapped[Optional[str]] = mapped_column(String(128))
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        Index("ix_order_items_order_id", "order_id"),
        Index("ix_order_items_product_id", "product_id"),
        Index("ix_order_items_feedback_due_at", "feedback_due_at"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    order_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    product_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price_snapshot: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    name_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    platform_snapshot: Mapped[Optional[str]] = mapped_column(String(64))
    product_url_snapshot: Mapped[Optional[str]] = mapped_column(String(1024))
    feedback_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    feedback_submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    feedback_prompt_dismissed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
