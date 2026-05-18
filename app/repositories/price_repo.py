"""Price history repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.price_history import PriceHistory


class PriceHistoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_product(self, product_id: int, limit: int = 30) -> list[PriceHistory]:
        statement = (
            select(PriceHistory)
            .where(PriceHistory.product_id == product_id)
            .order_by(PriceHistory.date.desc(), PriceHistory.id.desc())
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())
