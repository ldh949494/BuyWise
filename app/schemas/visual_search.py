"""Visual product search schemas."""

from __future__ import annotations

from pydantic import Field

from app.schemas.chat import ProductCard
from app.schemas.common import BaseSchema


class VisionRecognition(BaseSchema):
    category: str | None = None
    features: list[str] = Field(default_factory=list)
    query: str | None = None
    colors: list[str] = Field(default_factory=list)
    materials: list[str] = Field(default_factory=list)
    shape: str | None = None
    style: str | None = None
    brand_cues: list[str] = Field(default_factory=list)
    confidence: float | None = None
    detected_objects: list[str] = Field(default_factory=list)


class VisualSearchRequest(BaseSchema):
    image_url: str
    message: str | None = None
    top_k: int = Field(default=8, ge=1, le=30)


class VisualMatch(BaseSchema):
    product_id: int
    image_url: str | None = None
    score: float
    source: str


class VisualSearchResponse(BaseSchema):
    recognized: VisionRecognition
    products: list[ProductCard] = Field(default_factory=list)
    match_reasons: dict[int, list[str]] = Field(default_factory=dict)
    visual_matches: list[VisualMatch] = Field(default_factory=list)
    fallback_used: bool = False
