"""Admin API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.schemas.common import BaseSchema
from app.schemas.product import ProductRead


class AdminLoginRequest(BaseSchema):
    username: str
    password: str


class AdminTokenResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AdminProductWriteResponse(BaseSchema):
    product: ProductRead
    index_sync_status: str = "attempted"
    index_sync_note: str = "Product index sync is best-effort; check logs if search results do not update."


class AdminOrderAudit(BaseSchema):
    id: int
    user_ref: str
    payment_status: str
    fulfillment_status: str
    external_platform: str | None = None
    external_order_ref: str | None = None
    created_at: datetime


class AdminFeedbackAudit(BaseSchema):
    order_id: int
    order_item_id: int
    user_ref: str
    product_id: int
    product_name: str
    feedback_due_at: datetime | None = None


class AdminReviewAudit(BaseSchema):
    id: int
    product_id: int | None = None
    order_item_id: int | None = None
    user_ref: str | None = None
    rating: float | None = None
    purchase_evidence: str | None = None
    status: str | None = None
    created_at: datetime | None = None


class AdminOpsSummary(BaseSchema):
    readiness: dict[str, Any]
    index_health: dict[str, Any]
    catalog: dict[str, Any]
    token_guidance: list[dict[str, Any]]
    operations: list[dict[str, str]]
    recent_orders: list[AdminOrderAudit]
    pending_feedback: list[AdminFeedbackAudit]
    recent_reviews: list[AdminReviewAudit]
