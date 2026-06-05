"""Chat stream event schemas."""

from pydantic import Field

from app.schemas.chat import BundlePlan, ProductCard, StructuredNeed
from app.schemas.common import BaseSchema


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


class ChatStreamDoneEventData(BaseSchema):
    reply: str
    degraded: bool = False
    degraded_reason: str | None = None


class ChatStreamErrorEventData(BaseSchema):
    code: str
    message: str
    session_id: str
