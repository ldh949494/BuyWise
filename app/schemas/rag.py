"""RAG request and response schemas."""

from typing import Any

from pydantic import Field

from app.schemas.common import BaseSchema


class RagSearchRequest(BaseSchema):
    query: str
    top_k: int = 5
    filters: dict[str, Any] = Field(default_factory=dict)


class RagItem(BaseSchema):
    product_id: int
    name: str
    price: float | None = None
    score: float | None = None
    reason: str | None = None
    category: str | None = None
    platform: str | None = None
    product_url: str | None = None
    stock_status: str | None = None


class RagSearchResponse(BaseSchema):
    query: str
    items: list[RagItem] = Field(default_factory=list)
    total: int = 0
