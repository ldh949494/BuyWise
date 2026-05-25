"""Order and post-delivery feedback workflow service."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.providers import AppError
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.review import Review
from app.repositories.order_repo import OrderRepository
from app.repositories.product_repo import ProductRepository
from app.repositories.review_repo import ReviewRepository
from app.schemas.order import FeedbackPromptRead, OrderCreate, OrderItemRead, OrderRead
from app.schemas.review import ReviewFromOrderItemCreate, ReviewUpdate


class PaymentStatus:
    PAID = "paid"
    CANCELLED = "cancelled"


class FulfillmentStatus:
    PENDING = "pending"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class ReviewSource:
    POST_DELIVERY = "buywise_post_delivery"


class PurchaseEvidence:
    BUYWISE_RECORDED = "buywise_recorded"


class ReviewStatus:
    ACTIVE = "active"
    WITHDRAWN = "withdrawn"


def get_current_user_ref(subject: str | None) -> str:
    return (subject or settings.demo_user_ref).strip() or "demo-user"


class OrderService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.orders = OrderRepository(db)
        self.products = ProductRepository(db)

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
        order = Order(
            user_ref=user_ref,
            payment_status=PaymentStatus.PAID,
            fulfillment_status=FulfillmentStatus.PENDING,
            external_platform=payload.external_platform or product.platform,
            external_order_ref=payload.external_order_ref,
            paid_at=now,
            created_at=now,
            updated_at=now,
        )
        item = OrderItem(
            order_id=0,
            product_id=product.id,
            quantity=payload.quantity,
            unit_price_snapshot=Decimal(product.price),
            name_snapshot=product.name,
            platform_snapshot=product.platform,
            product_url_snapshot=product.product_url,
            created_at=now,
        )
        return order, item

    def list_orders(self, user_ref: str) -> list[OrderRead]:
        return [self._read_order(order) for order in self.orders.list_for_user(user_ref)]

    def get_order(self, order_id: int, user_ref: str) -> OrderRead:
        order = self._get_order(order_id, user_ref)
        return self._read_order(order)

    def update_order_progress(self, order_id: int, user_ref: str) -> OrderRead:
        order = self._get_order(order_id, user_ref)
        now = datetime.utcnow()
        if order.fulfillment_status == FulfillmentStatus.PENDING:
            order.fulfillment_status = FulfillmentStatus.SHIPPED
            order.shipped_at = now
        elif order.fulfillment_status == FulfillmentStatus.SHIPPED:
            order.fulfillment_status = FulfillmentStatus.DELIVERED
            order.delivered_at = now
            for item in self.orders.list_items(order.id):
                item.feedback_due_at = now + timedelta(days=settings.feedback_delay_days)
        elif order.fulfillment_status == FulfillmentStatus.DELIVERED:
            return self._read_order(order)
        else:
            raise AppError("Order cannot be advanced", status_code=409, code="invalid_order_state")
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


class ReviewWorkflowService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.orders = OrderRepository(db)
        self.reviews = ReviewRepository(db)

    def create_from_order_item(self, payload: ReviewFromOrderItemCreate, user_ref: str) -> Review:
        item, order = self._delivered_item(payload.order_item_id, user_ref)
        if self.reviews.get_active_for_order_item(item.id) is not None:
            raise AppError("Feedback already exists for this order item", status_code=409, code="duplicate_feedback")
        now = datetime.utcnow()
        review = self._build_review(payload, item, user_ref, now)
        _ = order
        try:
            review = self.reviews.create(review)
            item.feedback_submitted_at = now
            self.db.commit()
            self.db.refresh(review)
            return review
        except Exception:
            self.db.rollback()
            raise

    def _build_review(
        self,
        payload: ReviewFromOrderItemCreate,
        item: OrderItem,
        user_ref: str,
        now: datetime,
    ) -> Review:
        review = Review(
            product_id=item.product_id,
            order_item_id=item.id,
            user_ref=user_ref,
            rating=Decimal(payload.rating),
            content=payload.content.strip(),
            sentiment=self._sentiment(payload.rating),
            source=ReviewSource.POST_DELIVERY,
            verified_purchase=False,
            purchase_evidence=PurchaseEvidence.BUYWISE_RECORDED,
            usage_context=payload.usage_context,
            pros_tags=payload.pros_tags,
            cons_tags=payload.cons_tags,
            met_expectation=payload.met_expectation,
            status=ReviewStatus.ACTIVE,
            submitted_at=now,
            updated_at=now,
            created_at=now,
        )
        return review

    def update_review(self, review_id: int, payload: ReviewUpdate, user_ref: str) -> Review:
        review = self._active_review(review_id, user_ref)
        data = payload.model_dump(exclude_unset=True)
        if "rating" in data and data["rating"] is not None:
            review.rating = Decimal(data["rating"])
            review.sentiment = self._sentiment(data["rating"])
        for field in ["content", "usage_context", "pros_tags", "cons_tags", "met_expectation"]:
            if field in data:
                value = data[field]
                if field == "content" and value is not None:
                    value = value.strip()
                setattr(review, field, value)
        review.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(review)
        return review

    def update_review_withdrawn(self, review_id: int, user_ref: str) -> Review:
        review = self._active_review(review_id, user_ref)
        review.status = ReviewStatus.WITHDRAWN
        review.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(review)
        return review

    def _delivered_item(self, order_item_id: int, user_ref: str) -> tuple[OrderItem, Order]:
        row = self.orders.get_item_for_user(order_item_id, user_ref)
        if row is None:
            raise AppError("Order item not found", status_code=404, code="not_found")
        item, order = row
        if order.fulfillment_status != FulfillmentStatus.DELIVERED:
            raise AppError("Order item is not delivered", status_code=409, code="not_delivered")
        return item, order

    def _active_review(self, review_id: int, user_ref: str) -> Review:
        review = self.reviews.get_by_id_for_user(review_id, user_ref)
        if review is None:
            raise AppError("Review not found", status_code=404, code="not_found")
        if review.status != ReviewStatus.ACTIVE:
            raise AppError("Review is not active", status_code=409, code="inactive_review")
        return review

    def _sentiment(self, rating: int) -> str:
        if rating >= 4:
            return "positive"
        if rating == 3:
            return "neutral"
        return "negative"
