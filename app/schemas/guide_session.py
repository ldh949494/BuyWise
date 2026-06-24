"""Guide chat session API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.common import BaseSchema


class GuideSessionCreateResponse(BaseSchema):
    session_id: str
    session_token: str | None = None


class GuideSessionSummary(BaseSchema):
    session_id: str
    title: str | None = None
    updated_at: datetime | None = None
    created_at: datetime | None = None
    last_message: str | None = None


class GuideSessionListResponse(BaseSchema):
    items: list[GuideSessionSummary] = Field(default_factory=list)


class GuideSessionMessage(BaseSchema):
    role: str | None = None
    content: str | None = None
    created_at: datetime | None = None
    products: list[dict[str, Any]] = Field(default_factory=list)
    bundle_plans: list[dict[str, Any]] = Field(default_factory=list)
    applied_preferences: dict[str, Any] = Field(default_factory=dict)
    turn_type: str | None = None


class GuideSessionDetail(BaseSchema):
    session_id: str
    title: str | None = None
    messages: list[GuideSessionMessage] = Field(default_factory=list)
