"""Order repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.order import Order, OrderItem


class OrderRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, order: Order, item: OrderItem) -> Order:
        self.db.add(order)
        self.db.flush()
        item.order_id = order.id
        self.db.add(item)
        self.db.flush()
        return order

    def get_for_user(self, order_id: int, user_ref: str) -> Order | None:
        return self.db.scalar(select(Order).where(Order.id == order_id, Order.user_ref == user_ref))

    def list_for_user(self, user_ref: str) -> list[Order]:
        statement = select(Order).where(Order.user_ref == user_ref).order_by(Order.created_at.desc(), Order.id.desc())
        return list(self.db.scalars(statement).all())

    def list_items(self, order_id: int) -> list[OrderItem]:
        statement = select(OrderItem).where(OrderItem.order_id == order_id).order_by(OrderItem.id)
        return list(self.db.scalars(statement).all())

    def get_item_for_user(self, order_item_id: int, user_ref: str) -> tuple[OrderItem, Order] | None:
        statement = (
            select(OrderItem, Order)
            .join(Order, Order.id == OrderItem.order_id)
            .where(OrderItem.id == order_item_id, Order.user_ref == user_ref)
        )
        row = self.db.execute(statement).first()
        if row is None:
            return None
        return row[0], row[1]

    def list_due_feedback_items(self, user_ref: str, now) -> list[tuple[OrderItem, Order]]:
        statement = (
            select(OrderItem, Order)
            .join(Order, Order.id == OrderItem.order_id)
            .where(
                Order.user_ref == user_ref,
                Order.fulfillment_status == "delivered",
                OrderItem.feedback_due_at.is_not(None),
                OrderItem.feedback_due_at <= now,
                OrderItem.feedback_submitted_at.is_(None),
                OrderItem.feedback_prompt_dismissed_at.is_(None),
            )
            .order_by(OrderItem.feedback_due_at.asc(), OrderItem.id.asc())
        )
        return [(row[0], row[1]) for row in self.db.execute(statement).all()]
