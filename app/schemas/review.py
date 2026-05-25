"""Review request and response schemas."""

from datetime import datetime

from pydantic import Field, field_validator

from app.schemas.common import BaseSchema


PRO_TAGS = {"durable", "comfortable", "portable", "quiet", "good_value", "easy_to_use"}
CON_TAGS = {"fragile", "uncomfortable", "heavy", "noisy", "overpriced", "hard_to_use"}


class ReviewFromOrderItemCreate(BaseSchema):
    order_item_id: int
    rating: int = Field(ge=1, le=5)
    content: str = Field(min_length=5)
    usage_context: str | None = Field(default=None, max_length=64)
    pros_tags: list[str] = Field(default_factory=list)
    cons_tags: list[str] = Field(default_factory=list)
    met_expectation: bool | None = None

    @field_validator("pros_tags")
    @classmethod
    def validate_pro_tags(cls, value: list[str]) -> list[str]:
        unknown = sorted(set(value) - PRO_TAGS)
        if unknown:
            raise ValueError(f"Unknown pro tags: {', '.join(unknown)}")
        return value

    @field_validator("cons_tags")
    @classmethod
    def validate_con_tags(cls, value: list[str]) -> list[str]:
        unknown = sorted(set(value) - CON_TAGS)
        if unknown:
            raise ValueError(f"Unknown con tags: {', '.join(unknown)}")
        return value


class ReviewUpdate(BaseSchema):
    rating: int | None = Field(default=None, ge=1, le=5)
    content: str | None = Field(default=None, min_length=5)
    usage_context: str | None = Field(default=None, max_length=64)
    pros_tags: list[str] | None = None
    cons_tags: list[str] | None = None
    met_expectation: bool | None = None

    @field_validator("pros_tags")
    @classmethod
    def validate_optional_pro_tags(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        unknown = sorted(set(value) - PRO_TAGS)
        if unknown:
            raise ValueError(f"Unknown pro tags: {', '.join(unknown)}")
        return value

    @field_validator("cons_tags")
    @classmethod
    def validate_optional_con_tags(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        unknown = sorted(set(value) - CON_TAGS)
        if unknown:
            raise ValueError(f"Unknown con tags: {', '.join(unknown)}")
        return value


class ReviewRead(BaseSchema):
    id: int
    product_id: int | None = None
    order_item_id: int | None = None
    user_ref: str | None = None
    rating: float | None = None
    content: str | None = None
    sentiment: str | None = None
    source: str | None = None
    verified_purchase: bool | None = None
    purchase_evidence: str | None = None
    usage_context: str | None = None
    pros_tags: list[str] = Field(default_factory=list)
    cons_tags: list[str] = Field(default_factory=list)
    met_expectation: bool | None = None
    status: str | None = None
    submitted_at: datetime | None = None
    updated_at: datetime | None = None
    created_at: datetime | None = None
