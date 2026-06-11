"""Chat stream event schemas."""

from typing import Any

from pydantic import Field

from app.schemas.chat import BundlePlan, ProductCard, StructuredNeed
from app.schemas.common import BaseSchema
from app.schemas.guide_preferences import AppliedPreferences


class ChatStreamMetaEventData(BaseSchema):
    session_id: str


class ChatStreamStatusEventData(BaseSchema):
    stage: str
    message: str


class ChatStreamTokenEventData(BaseSchema):
    text: str


class ChatStreamProductsEventData(BaseSchema):
    need_clarify: bool = False
    structured_need: StructuredNeed
    items: list[ProductCard] = Field(default_factory=list)
    bundle_plans: list[BundlePlan] = Field(default_factory=list)
    applied_preferences: AppliedPreferences = Field(default_factory=AppliedPreferences)
    fallback_used: bool = False
    fallback_stage: str | None = None
    result_quality: str = "exact"


class ChatStreamDoneEventData(BaseSchema):
    reply: str
    degraded: bool = False
    degraded_reason: str | None = None
    should_refresh: bool = False
    refresh_reason: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class ChatStreamErrorEventData(BaseSchema):
    code: str
    message: str
    session_id: str
