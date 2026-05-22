"""Price history repository."""

from __future__ import annotations

from sqlalchemy import func, select
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

    def get_average_by_product_ids(self, product_ids: list[int]) -> dict[int, float]:
        if not product_ids:
            return {}
        statement = (
            select(PriceHistory.product_id, func.avg(PriceHistory.price))
            .where(PriceHistory.product_id.in_(product_ids))
            .group_by(PriceHistory.product_id)
        )
        return {int(product_id): float(value) for product_id, value in self.db.execute(statement) if value is not None}
