"""Product persistence model."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import BigInteger, DateTime, Index, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        Index("ix_products_category", "category"),
        Index("ix_products_price", "price"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(64))
    brand: Mapped[Optional[str]] = mapped_column(String(64))
    sku: Mapped[Optional[str]] = mapped_column(String(128))
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    original_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    platform: Mapped[Optional[str]] = mapped_column(String(64))
    product_url: Mapped[Optional[str]] = mapped_column(String(1024))
    image_url: Mapped[Optional[str]] = mapped_column(String(512))
    image_urls: Mapped[Optional[Any]] = mapped_column(JSON)
    rating: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))
    sales: Mapped[Optional[int]] = mapped_column(Integer)
    description: Mapped[Optional[str]] = mapped_column(Text)
    specs: Mapped[Optional[Any]] = mapped_column(JSON)
    tags: Mapped[Optional[Any]] = mapped_column(JSON)
    suitable_scene: Mapped[Optional[Any]] = mapped_column(JSON)
    stock: Mapped[Optional[int]] = mapped_column(Integer)
    stock_status: Mapped[Optional[str]] = mapped_column(String(32))
    review_summary: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
