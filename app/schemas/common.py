from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseSchema):
    status: str
    service: str


class ErrorResponse(BaseSchema):
    detail: str
    code: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)
