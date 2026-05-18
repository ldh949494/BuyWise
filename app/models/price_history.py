"""Price history persistence model."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, Date, Index, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PriceHistory(Base):
    __tablename__ = "price_history"
    __table_args__ = (
        Index("ix_price_history_product_id", "product_id"),
        Index("ix_price_history_date", "date"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    product_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    date: Mapped[Optional[date]] = mapped_column(Date)
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
