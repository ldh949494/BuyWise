"""RAG request and response schemas."""

from typing import Any

from pydantic import Field

from app.schemas.common import BaseSchema


class RagSearchRequest(BaseSchema):
    query: str
    top_k: int = 5
    filters: dict[str, Any] = Field(default_factory=dict)


class RagSearchResponse(BaseSchema):
    query: str
    items: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0
