"""Chat request and response schemas."""

from typing import Any

from pydantic import Field

from app.schemas.common import BaseSchema
from app.schemas.guide_preferences import AppliedPreferences, GuidePreferences


class ChatRequest(BaseSchema):
    session_id: str | None = None
    session_token: str | None = Field(default=None, min_length=16)
    message: str | None = None
    image_url: str | None = None
    audio_url: str | None = None
    ignore_saved_preferences: bool = False
    temporary_preferences: GuidePreferences | None = None


class StructuredNeed(BaseSchema):
    intent: str
    category: str | None = None
    budget_max: float | None = None
    scenario: str | None = None
    target_date: str | None = None
    location: str | None = None
    duration_days: int | None = None
    occasion: str | None = None
    preferences: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)
    style_preferences: list[str] = Field(default_factory=list)
    must_have_categories: list[str] = Field(default_factory=list)
    excluded_categories: list[str] = Field(default_factory=list)
    budget_policy: str | None = None
    budget_flex_rate: float | None = None
    presentation_style: str | None = None
    owned_categories: list[str] = Field(default_factory=list)
    purchase_stage: str = "consider"
    retrieval_strategy: str = "balanced"
    need_clarify: bool = False
    missing_fields: list[str] = Field(default_factory=list)


class ProductCard(BaseSchema):
    id: int
    name: str
    price: float
    category: str | None = None
    platform: str | None = None
    product_url: str | None = None
    stock_status: str | None = None
    image_url: str | None = None
    rating: float | None = None
    score: float | None = None
    tags: list[str] = Field(default_factory=list)
    reason: str | None = None
    budget_match: bool | None = None
    scenario_match: bool | None = None
    conflicts: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)


class BundleCompleteness(BaseSchema):
    included_required: int = 0
    expected_required: int = 0
    optional_included: int = 0
    missing: list[str] = Field(default_factory=list)
    needs_confirmation: list[str] = Field(default_factory=list)


class BundleBudgetAllocation(BaseSchema):
    category: str
    amount: float


class BundleCompatibilityCheck(BaseSchema):
    title: str
    status: str
    message: str


class BundlePlanItem(BaseSchema):
    category: str
    product: ProductCard
    role: str | None = None
    required: bool = True
    replaceable: bool = True
    locked: bool = False
    excluded: bool = False


class BundlePlan(BaseSchema):
    id: str
    title: str
    budget_tier: str
    target_budget: float | None = None
    total_price: float
    budget_status: str
    budget_delta: float | None = None
    recommendation_level: str = "medium"
    scenario_fit: str | None = None
    summary: str | None = None
    completeness: BundleCompleteness = Field(default_factory=BundleCompleteness)
    budget_allocation: list[BundleBudgetAllocation] = Field(default_factory=list)
    items: list[BundlePlanItem] = Field(default_factory=list)
    tradeoffs: list[str] = Field(default_factory=list)
    compare_highlights: list[str] = Field(default_factory=list)
    exclusion_notes: list[str] = Field(default_factory=list)
    compatibility_checks: list[BundleCompatibilityCheck] = Field(default_factory=list)
    price_checked_at: str | None = None
    availability_status: str = "available"
    revision: int = 1


class ChatResponse(BaseSchema):
    reply: str
    need_clarify: bool = False
    structured_need: StructuredNeed | None = None
    products: list[ProductCard] = Field(default_factory=list)
    bundle_plans: list[BundlePlan] = Field(default_factory=list)
    applied_preferences: AppliedPreferences = Field(default_factory=AppliedPreferences)
    extra: dict[str, Any] = Field(default_factory=dict)
