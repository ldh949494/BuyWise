"""Guide conversation turn state and routing decisions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.schemas.chat import StructuredNeed
from app.utils.guide_turn import list_string_values


@dataclass(frozen=True)
class GuideSnapshot:
    need: dict[str, Any]
    products: list[dict[str, Any]] = field(default_factory=list)
    bundle_plans: list[dict[str, Any]] = field(default_factory=list)
    applied_preferences: dict[str, Any] = field(default_factory=dict)
    created_at: Any | None = None


@dataclass(frozen=True)
class GuideConversationState:
    active_snapshot: GuideSnapshot | None = None

    def get_has_active_recommendation(self) -> bool:
        return self.active_snapshot is not None


@dataclass(frozen=True)
class GuideTurnDecision:
    turn_type: str
    reason: str
    need: StructuredNeed | None = None
    snapshot: GuideSnapshot | None = None

    def get_should_recommend(self) -> bool:
        return self.turn_type in {"new_recommendation", "refresh_recommendation"}

    def get_should_answer_snapshot(self) -> bool:
        return self.turn_type == "answer_snapshot"


class GuideConversationStateBuilder:
    def build(self, messages: list[Any]) -> GuideConversationState:
        for message in reversed(messages):
            structured_data = getattr(message, "structured_data", None) or {}
            snapshot = self._snapshot_from_structured_data(structured_data, getattr(message, "created_at", None))
            if snapshot is not None:
                return GuideConversationState(active_snapshot=snapshot)
        return GuideConversationState()

    def _snapshot_from_structured_data(self, structured_data: dict[str, Any], created_at: Any | None) -> GuideSnapshot | None:
        if not isinstance(structured_data, dict):
            return None
        products = structured_data.get("products") or []
        bundle_plans = structured_data.get("bundle_plans") or []
        need = structured_data.get("need")
        if not isinstance(need, dict) or not (products or bundle_plans):
            return None
        return GuideSnapshot(
            need=need,
            products=[product for product in products if isinstance(product, dict)],
            bundle_plans=[plan for plan in bundle_plans if isinstance(plan, dict)],
            applied_preferences=structured_data.get("applied_preferences") or {},
            created_at=created_at,
        )


class GuideTurnClassifier:
    BUNDLE_INTENTS = {"bundle_recommend", "场景化组合推荐"}
    CHANGE_MARKERS = [
        "重新推荐",
        "重新生成推荐",
        "重新生成",
        "重新导购",
        "换一个",
        "换一批",
        "换品类",
        "换预算",
        "提高预算",
        "降低预算",
        "预算提高",
        "预算降低",
        "再推荐",
        "重新选",
        "不要这些",
        "改成",
        "换成",
    ]
    RECOMMENDATION_MARKERS = ["推荐一个", "推荐一款", "推荐一下", "帮我推荐", "我要", "我想要", "想买", "需要一个"]

    def __init__(self, intent_service: Any) -> None:
        self.intent_service = intent_service

    async def build_decision(
        self,
        *,
        text: str,
        image_info: dict | None,
        history_context: dict[str, Any],
        state: GuideConversationState,
    ) -> GuideTurnDecision:
        need = await self.intent_service.extract(text, image_info=image_info, history_context=history_context)
        return self.build_decision_for_need(text=text, need=need, state=state)

    def build_decision_for_need(self, *, text: str, need: StructuredNeed, state: GuideConversationState) -> GuideTurnDecision:
        if not state.get_has_active_recommendation():
            return GuideTurnDecision("new_recommendation", "missing_active_snapshot", need=need)
        if need.need_clarify:
            return GuideTurnDecision("clarify", "need_clarify", need=need, snapshot=state.active_snapshot)
        if self._is_condition_change(text, need, state.active_snapshot):
            return GuideTurnDecision("refresh_recommendation", "condition_changed", need=need, snapshot=state.active_snapshot)
        return GuideTurnDecision("answer_snapshot", "snapshot_question", need=need, snapshot=state.active_snapshot)

    def _is_condition_change(self, text: str, need: StructuredNeed, snapshot: GuideSnapshot | None) -> bool:
        if snapshot is None:
            return True
        normalized = text.strip().lower()
        if any(marker in normalized for marker in self.CHANGE_MARKERS):
            return True
        if self._bundle_condition_changed(need, snapshot):
            return True
        if self._changed_structured_fields(need, snapshot.need):
            return True
        snapshot_category = str(snapshot.need.get("category") or "").strip()
        if any(marker in normalized for marker in self.RECOMMENDATION_MARKERS):
            return bool(need.category and need.category != snapshot_category)
        return False

    def _bundle_condition_changed(self, need: StructuredNeed, snapshot: GuideSnapshot) -> bool:
        if need.intent not in self.BUNDLE_INTENTS:
            return False
        requested_categories = set(list_string_values(need.must_have_categories))
        if not requested_categories:
            return False
        prior_categories = set(list_string_values(snapshot.need.get("must_have_categories")))
        if requested_categories != prior_categories:
            return True
        return snapshot.need.get("intent") not in self.BUNDLE_INTENTS

    def _changed_structured_fields(self, need: StructuredNeed, snapshot_need: dict[str, Any]) -> bool:
        for field_name in ["category", "budget_max", "scenario"]:
            before = snapshot_need.get(field_name)
            after = getattr(need, field_name, None)
            if before not in (None, [], "") and after not in (None, [], "") and before != after:
                return True
        for field_name in ["preferences", "avoid", "style_preferences", "excluded_categories"]:
            before_values = set(list_string_values(snapshot_need.get(field_name)))
            after_values = set(list_string_values(getattr(need, field_name, [])))
            if before_values != after_values:
                return True
        return False
