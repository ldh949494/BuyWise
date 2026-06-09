"""Order request and response schemas."""

from datetime import datetime

from pydantic import Field

from app.schemas.common import BaseSchema


class OrderCreate(BaseSchema):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=99)
    external_platform: str | None = Field(default=None, max_length=64)
    external_order_ref: str | None = Field(default=None, max_length=128)


class OrderItemRead(BaseSchema):
    id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price_snapshot: float
    name_snapshot: str
    platform_snapshot: str | None = None
    product_url_snapshot: str | None = None
    feedback_due_at: datetime | None = None
    feedback_submitted_at: datetime | None = None
    feedback_prompt_dismissed_at: datetime | None = None
    created_at: datetime


class OrderRead(BaseSchema):
    id: int
    user_ref: str
    payment_status: str
    fulfillment_status: str
    external_platform: str | None = None
    external_order_ref: str | None = None
    checkout_session_id: int | None = None
    source_session_id: str | None = None
    payment_mode: str | None = None
    address_snapshot: dict | None = None
    cart_snapshot: dict | None = None
    total_price_snapshot: float | None = None
    paid_at: datetime | None = None
    shipped_at: datetime | None = None
    delivered_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemRead] = Field(default_factory=list)


class OrderListResponse(BaseSchema):
    items: list[OrderRead] = Field(default_factory=list)


class FeedbackPromptRead(BaseSchema):
    order_id: int
    order_item_id: int
    product_id: int
    product_name: str
    feedback_due_at: datetime
    delivered_at: datetime | None = None


class FeedbackPromptListResponse(BaseSchema):
    items: list[FeedbackPromptRead] = Field(default_factory=list)
