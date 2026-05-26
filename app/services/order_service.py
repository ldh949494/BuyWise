"""Order and post-delivery feedback workflow service."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.providers import AppError
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.repositories.order_repo import OrderRepository
from app.repositories.product_repo import ProductRepository
from app.schemas.order import FeedbackPromptRead, OrderCreate, OrderItemRead, OrderRead
from app.services.policies.order_state_machine import FulfillmentStatus, OrderStateMachine, PaymentStatus


def get_current_user_ref(subject: str | None) -> str:
    return (subject or settings.demo_user_ref).strip() or "demo-user"


class OrderService:
    def __init__(self, db: Session, state_machine: OrderStateMachine | None = None) -> None:
        self.db = db
        self.orders = OrderRepository(db)
        self.products = ProductRepository(db)
        self.state_machine = state_machine or OrderStateMachine(feedback_delay_days=settings.feedback_delay_days)

    def create_order(self, payload: OrderCreate, user_ref: str) -> OrderRead:
        product = self._purchasable_product(payload.product_id)
        now = datetime.utcnow()
        order, item = self._build_order_and_item(payload, user_ref, product, now)
        try:
            order = self.orders.create(order, item)
            self.db.commit()
            self.db.refresh(order)
            return self._read_order(order)
        except Exception:
            self.db.rollback()
            raise

    def _build_order_and_item(
        self,
        payload: OrderCreate,
        user_ref: str,
        product: Product,
        now: datetime,
    ) -> tuple[Order, OrderItem]:
        state = self.state_machine.build_initial_order_state(
            external_purchase=self._is_external_purchase(payload),
            external_feedback_mode=settings.external_purchase_feedback_mode,
            now=now,
        )
        order = self._build_order(payload, user_ref, product, state.fulfillment_status, state.delivered_at, now)
        item = self._build_order_item(payload, product, state.feedback_due_at, now)
        return order, item

    def _build_order(
        self,
        payload: OrderCreate,
        user_ref: str,
        product: Product,
        fulfillment_status: str,
        delivered_at: datetime | None,
        now: datetime,
    ) -> Order:
        order = Order(
            user_ref=user_ref,
            payment_status=PaymentStatus.PAID,
            fulfillment_status=fulfillment_status,
            external_platform=payload.external_platform or product.platform,
            external_order_ref=payload.external_order_ref,
            paid_at=now,
            delivered_at=delivered_at,
            created_at=now,
            updated_at=now,
        )

        return order

    def _build_order_item(
        self,
        payload: OrderCreate,
        product: Product,
        feedback_due_at: datetime | None,
        now: datetime,
    ) -> OrderItem:
        return OrderItem(
            order_id=0,
            product_id=product.id,
            quantity=payload.quantity,
            unit_price_snapshot=Decimal(product.price),
            name_snapshot=product.name,
            platform_snapshot=product.platform,
            product_url_snapshot=product.product_url,
            feedback_due_at=feedback_due_at,
            created_at=now,
        )

    def _is_external_purchase(self, payload: OrderCreate) -> bool:
        return bool((payload.external_platform or "").strip())

    def list_orders(self, user_ref: str) -> list[OrderRead]:
        return [self._read_order(order) for order in self.orders.list_for_user(user_ref)]

    def get_order(self, order_id: int, user_ref: str) -> OrderRead:
        order = self._get_order(order_id, user_ref)
        return self._read_order(order)

    def update_order_progress(self, order_id: int, user_ref: str) -> OrderRead:
        order = self._get_order(order_id, user_ref)
        now = datetime.utcnow()
        transition = self.state_machine.build_transition(order.fulfillment_status, now=now)
        if not transition.valid:
            raise AppError("Order cannot be advanced", status_code=409, code="invalid_order_state")
        if transition.no_op:
            return self._read_order(order)
        if transition.fulfillment_status is not None:
            order.fulfillment_status = transition.fulfillment_status
        if transition.shipped_at is not None:
            order.shipped_at = transition.shipped_at
        if transition.delivered_at is not None:
            order.delivered_at = transition.delivered_at
        if transition.item_feedback_due_at is not None:
            for item in self.orders.list_items(order.id):
                item.feedback_due_at = transition.item_feedback_due_at
        order.updated_at = now
        self.db.commit()
        self.db.refresh(order)
        return self._read_order(order)

    def update_feedback_prompt_dismissed(self, order_item_id: int, user_ref: str) -> None:
        row = self.orders.get_item_for_user(order_item_id, user_ref)
        if row is None:
            raise AppError("Order item not found", status_code=404, code="not_found")
        item, _ = row
        item.feedback_prompt_dismissed_at = datetime.utcnow()
        self.db.commit()

    def list_due_feedback_prompts(self, user_ref: str) -> list[FeedbackPromptRead]:
        prompts = []
        for item, order in self.orders.list_due_feedback_items(user_ref, datetime.utcnow()):
            prompts.append(
                FeedbackPromptRead(
                    order_id=order.id,
                    order_item_id=item.id,
                    product_id=item.product_id,
                    product_name=item.name_snapshot,
                    feedback_due_at=item.feedback_due_at,
                    delivered_at=order.delivered_at,
                )
            )
        return prompts

    def _purchasable_product(self, product_id: int) -> Product:
        product = self.products.get_by_id(product_id)
        if product is None:
            raise AppError("Product not found", status_code=404, code="not_found")
        if product.stock_status == "out_of_stock":
            raise AppError("Product is out of stock", status_code=409, code="out_of_stock")
        if product.price is None:
            raise AppError("Product price is required", status_code=409, code="missing_price")
        return product

    def _get_order(self, order_id: int, user_ref: str) -> Order:
        order = self.orders.get_for_user(order_id, user_ref)
        if order is None:
            raise AppError("Order not found", status_code=404, code="not_found")
        return order

    def _read_order(self, order: Order) -> OrderRead:
        items = [OrderItemRead.model_validate(item) for item in self.orders.list_items(order.id)]
        return OrderRead(
            id=order.id,
            user_ref=order.user_ref,
            payment_status=order.payment_status,
            fulfillment_status=order.fulfillment_status,
            external_platform=order.external_platform,
            external_order_ref=order.external_order_ref,
            paid_at=order.paid_at,
            shipped_at=order.shipped_at,
            delivered_at=order.delivered_at,
            created_at=order.created_at,
            updated_at=order.updated_at,
            items=items,
        )
