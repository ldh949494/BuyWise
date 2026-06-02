"""Chat request and response schemas."""

from typing import Any

from pydantic import Field

from app.schemas.common import BaseSchema


class ChatRequest(BaseSchema):
    session_id: str | None = None
    message: str | None = None
    image_url: str | None = None
    audio_url: str | None = None


class StructuredNeed(BaseSchema):
    intent: str
    category: str | None = None
    budget_max: float | None = None
    scenario: str | None = None
    preferences: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)
    purchase_stage: str = "consider"
    retrieval_strategy: str = "balanced"
    need_clarify: bool = False
    missing_fields: list[str] = Field(default_factory=list)


class ProductCard(BaseSchema):
    id: int
    name: str
    price: float
    image_url: str | None = None
    rating: float | None = None
    score: float | None = None
    tags: list[str] = Field(default_factory=list)
    reason: str | None = None
    budget_match: bool | None = None
    scenario_match: bool | None = None
    conflicts: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)


class ChatResponse(BaseSchema):
    reply: str
    need_clarify: bool = False
    structured_need: StructuredNeed | None = None
    products: list[ProductCard] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)
