"""Comparison request and response schemas."""

from typing import Any

from pydantic import Field

from app.schemas.common import BaseSchema


class CompareRequest(BaseSchema):
    product_ids: list[int]
    session_id: str | None = None


class CompareItem(BaseSchema):
    id: int
    name: str
    price: float | None = None
    image_url: str | None = None
    rating: float | None = None
    score: float | None = None
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    specs: dict[str, Any] = Field(default_factory=dict)


class CompareResponse(BaseSchema):
    items: list[CompareItem] = Field(default_factory=list)
    summary: str | None = None
    winner_id: int | None = None
