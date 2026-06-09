"""Cart, address, and checkout persistence models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Integer, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Cart(Base):
    __tablename__ = "carts"
    __table_args__ = (Index("ix_carts_user_ref", "user_ref", unique=True),)

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    user_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        Index("ix_cart_items_cart_id", "cart_id"),
        Index("ix_cart_items_product_id", "product_id"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    cart_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    product_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price_snapshot: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    name_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    image_url_snapshot: Mapped[Optional[str]] = mapped_column(String(512))
    platform_snapshot: Mapped[Optional[str]] = mapped_column(String(64))
    product_url_snapshot: Mapped[Optional[str]] = mapped_column(String(1024))
    source_session_id: Mapped[Optional[str]] = mapped_column(String(64))
    source_label: Mapped[Optional[str]] = mapped_column(String(128))
    locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class Address(Base):
    __tablename__ = "addresses"
    __table_args__ = (Index("ix_addresses_user_ref", "user_ref"),)

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    user_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    receiver_name: Mapped[str] = mapped_column(String(64), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    province: Mapped[Optional[str]] = mapped_column(String(64))
    city: Mapped[Optional[str]] = mapped_column(String(64))
    district: Mapped[Optional[str]] = mapped_column(String(64))
    detail: Mapped[str] = mapped_column(String(255), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class CheckoutSession(Base):
    __tablename__ = "checkout_sessions"
    __table_args__ = (
        Index("ix_checkout_sessions_user_ref", "user_ref"),
        Index("ix_checkout_sessions_order_id", "order_id"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    user_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    cart_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    order_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    address_snapshot: Mapped[Optional[Any]] = mapped_column(JSON)
    cart_snapshot: Mapped[Optional[Any]] = mapped_column(JSON)
    total_price_snapshot: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    source_session_id: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
