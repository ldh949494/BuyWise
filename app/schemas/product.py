"""Product request and response schemas."""

from datetime import date as Date
from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.common import BaseSchema


class ProductBase(BaseSchema):
    name: str | None = None
    category: str | None = None
    brand: str | None = None
    sku: str | None = None
    price: float | None = None
    original_price: float | None = None
    platform: str | None = None
    product_url: str | None = None
    image_url: str | None = None
    image_urls: list[str] = Field(default_factory=list)
    rating: float | None = None
    sales: int | None = None
    description: str | None = None
    specs: dict[str, Any] | list[Any] | None = None
    tags: list[str] = Field(default_factory=list)
    suitable_scene: list[str] = Field(default_factory=list)
    stock: int | None = None
    stock_status: str | None = None
    review_summary: str | None = None
    feedback_metrics: dict[str, Any] = Field(default_factory=dict)


class PriceHistoryRead(BaseSchema):
    date: Date | None = None
    price: float | None = None


class ProductCreate(ProductBase):
    name: str


class ProductUpdate(ProductBase):
    pass


class ProductRead(ProductBase):
    id: int
    name: str
    created_at: datetime | None = None
    price_history: list[PriceHistoryRead] = Field(default_factory=list)


class ProductListResponse(BaseSchema):
    items: list[ProductRead] = Field(default_factory=list)
    total: int
    page: int = 1
    page_size: int = 20
