"""Cart, address, and checkout schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.common import BaseSchema
from app.schemas.order import OrderRead


class CartItemCreate(BaseSchema):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=99)
    source_session_id: str | None = Field(default=None, max_length=64)
    source_label: str | None = Field(default=None, max_length=128)
    locked: bool = False


class CartItemUpdate(BaseSchema):
    quantity: int = Field(ge=1, le=99)


class CartItemRead(BaseSchema):
    id: int
    product_id: int
    quantity: int
    unit_price_snapshot: float
    line_total: float
    name_snapshot: str
    image_url_snapshot: str | None = None
    platform_snapshot: str | None = None
    product_url_snapshot: str | None = None
    source_session_id: str | None = None
    source_label: str | None = None
    locked: bool = False
    created_at: datetime
    updated_at: datetime


class CartRead(BaseSchema):
    id: int
    user_ref: str
    status: str
    total_quantity: int
    total_price: float
    items: list[CartItemRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class AddressCreate(BaseSchema):
    receiver_name: str = Field(min_length=1, max_length=64)
    phone: str = Field(min_length=3, max_length=32)
    province: str | None = Field(default=None, max_length=64)
    city: str | None = Field(default=None, max_length=64)
    district: str | None = Field(default=None, max_length=64)
    detail: str = Field(min_length=1, max_length=255)
    is_default: bool = False


class AddressRead(BaseSchema):
    id: int
    user_ref: str
    receiver_name: str
    phone: str
    province: str | None = None
    city: str | None = None
    district: str | None = None
    detail: str
    is_default: bool
    created_at: datetime
    updated_at: datetime


class AddressListResponse(BaseSchema):
    items: list[AddressRead] = Field(default_factory=list)


class CheckoutCreate(BaseSchema):
    address_id: int | None = None
    use_default_address: bool = True
    source_session_id: str | None = Field(default=None, max_length=64)


class CheckoutRead(BaseSchema):
    checkout_session_id: int
    order: OrderRead
    cart_cleared: bool = True


def decimal_to_float(value: Decimal | None) -> float:
    return float(value or Decimal("0"))
