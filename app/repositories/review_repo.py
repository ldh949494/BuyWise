"""Review repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.review import Review


class ReviewRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_product(self, product_id: int, limit: int = 20) -> list[Review]:
        statement = (
            select(Review)
            .where(Review.product_id == product_id)
            .order_by(Review.created_at.desc(), Review.id.desc())
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def build_summary_for_product(self, product_id: int, limit: int = 20) -> str | None:
        reviews = self.list_for_product(product_id, limit=limit)
        if not reviews:
            return None

        sentiments: dict[str, int] = {}
        highlights = []
        for review in reviews:
            if review.sentiment:
                sentiments[review.sentiment] = sentiments.get(review.sentiment, 0) + 1
            if review.content and len(highlights) < 3:
                highlights.append(review.content.strip())

        parts = []
        if sentiments:
            sentiment_text = ", ".join(f"{key}:{value}" for key, value in sorted(sentiments.items()))
            parts.append(f"sentiment {sentiment_text}")
        if highlights:
            parts.append(" | ".join(highlights))
        return "; ".join(parts) if parts else None
