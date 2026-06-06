"""Guide preference schemas."""

from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from app.schemas.common import BaseSchema

BudgetPolicy = Literal["strict", "slightly_flexible", "quality_first"]
PresentationStyle = Literal["direct_answer", "compare_options", "detailed_explanation"]


class BudgetRange(BaseSchema):
    min: float | None = Field(default=None, ge=0)
    max: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_range(self) -> "BudgetRange":
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("budget min cannot exceed max")
        return self


class GuidePreferences(BaseSchema):
    budget_policy: BudgetPolicy = "slightly_flexible"
    presentation_style: PresentationStyle = "compare_options"
    single_item_budgets: dict[str, BudgetRange] = Field(default_factory=dict)
    bundle_budget_range: BudgetRange | None = None
    priority_tags: list[str] = Field(default_factory=list)
    excluded_tags: list[str] = Field(default_factory=list)
    excluded_brands: list[str] = Field(default_factory=list)
    owned_categories: list[str] = Field(default_factory=list)
    extra_notes: str | None = None

    @field_validator("priority_tags", "excluded_tags", "excluded_brands", "owned_categories")
    @classmethod
    def normalize_list(cls, values: list[str]) -> list[str]:
        normalized = []
        seen = set()
        for value in values:
            clean = value.strip()
            if not clean or clean in seen:
                continue
            seen.add(clean)
            normalized.append(clean)
        return normalized

    @field_validator("extra_notes")
    @classmethod
    def normalize_extra_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        clean = value.strip()
        return clean or None


class GuidePreferencesUpdate(GuidePreferences):
    pass


class GuidePreferencesResponse(GuidePreferences):
    has_saved_preferences: bool = False


class AppliedPreferenceConstraint(BaseSchema):
    type: str
    key: str
    label: str
    effect: str


class AppliedPreferences(BaseSchema):
    used_saved_preferences: bool = False
    ignored_saved_preferences: bool = False
    budget_policy: BudgetPolicy | None = None
    presentation_style: PresentationStyle | None = None
    summary: list[str] = Field(default_factory=list)
    constraints: list[AppliedPreferenceConstraint] = Field(default_factory=list)


def preferences_json(preferences: GuidePreferences) -> dict[str, Any]:
    return preferences.model_dump(mode="json", exclude={"budget_policy", "presentation_style"})
