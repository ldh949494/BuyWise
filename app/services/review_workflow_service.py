"""Post-purchase review workflow service."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.metrics import count_feedback_submit_failure, count_feedback_submit_success
from app.core.providers import AppError
from app.models.order import Order, OrderItem
from app.models.review import Review
from app.repositories.order_repo import OrderRepository
from app.repositories.review_repo import ReviewRepository
from app.schemas.review import ReviewFromOrderItemCreate, ReviewUpdate
from app.services.order_service import FulfillmentStatus


class ReviewSource:
    POST_DELIVERY = "buywise_post_delivery"


class PurchaseEvidence:
    BUYWISE_RECORDED = "buywise_recorded"


class ReviewStatus:
    ACTIVE = "active"
    WITHDRAWN = "withdrawn"


class ReviewWorkflowService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.orders = OrderRepository(db)
        self.reviews = ReviewRepository(db)

    def create_from_order_item(self, payload: ReviewFromOrderItemCreate, user_ref: str) -> Review:
        try:
            item, _ = self._delivered_item(payload.order_item_id, user_ref)
            if self.reviews.get_active_for_order_item(item.id) is not None:
                raise AppError(
                    "Feedback already exists for this order item",
                    status_code=409,
                    code="duplicate_feedback",
                )
            return self._create_review(payload, item, user_ref)
        except AppError as exc:
            count_feedback_submit_failure(self._submit_failure_reason(exc.code))
            raise

    def _create_review(self, payload: ReviewFromOrderItemCreate, item: OrderItem, user_ref: str) -> Review:
        now = datetime.utcnow()
        review = self._build_review(payload, item, user_ref, now)
        try:
            review = self.reviews.create(review)
            item.feedback_submitted_at = now
            self.db.commit()
            self.db.refresh(review)
            count_feedback_submit_success("api")
            return review
        except SQLAlchemyError:
            self.db.rollback()
            count_feedback_submit_failure("db")
            raise

    def _build_review(
        self,
        payload: ReviewFromOrderItemCreate,
        item: OrderItem,
        user_ref: str,
        now: datetime,
    ) -> Review:
        return Review(
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

    def update_review(self, review_id: int, payload: ReviewUpdate, user_ref: str) -> Review:
        review = self._active_review(review_id, user_ref)
        self._apply_review_update(review, payload)
        self.db.commit()
        self.db.refresh(review)
        return review

    def _apply_review_update(self, review: Review, payload: ReviewUpdate) -> None:
        data = payload.model_dump(exclude_unset=True)
        if "rating" in data and data["rating"] is not None:
            review.rating = Decimal(data["rating"])
            review.sentiment = self._sentiment(data["rating"])
        for field in ["content", "usage_context", "pros_tags", "cons_tags", "met_expectation"]:
            if field in data:
                value = data[field].strip() if field == "content" and data[field] is not None else data[field]
                setattr(review, field, value)
        review.updated_at = datetime.utcnow()

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

    def _submit_failure_reason(self, code: str | None) -> str:
        return {
            "not_found": "not_found",
            "not_delivered": "validation",
            "duplicate_feedback": "validation",
        }.get(code or "", "unknown")
