"""Chat context extraction helpers."""

from __future__ import annotations

from typing import Any


class ChatContextService:
    CONTEXT_KEYS = [
        "intent",
        "category",
        "budget_max",
        "scenario",
        "target_date",
        "location",
        "duration_days",
        "occasion",
        "preferences",
        "avoid",
        "style_preferences",
        "must_have_categories",
        "excluded_categories",
        "budget_policy",
        "budget_flex_rate",
        "presentation_style",
        "owned_categories",
        "purchase_stage",
        "retrieval_strategy",
    ]

    def build_history_context(self, messages: list[Any]) -> dict[str, Any]:
        for message in reversed(messages):
            structured_data = getattr(message, "structured_data", None) or {}
            need = structured_data.get("need")
            if isinstance(need, dict):
                return self._need_context(need)
        return {}

    def _need_context(self, need: dict[str, Any]) -> dict[str, Any]:
        return {
            key: need.get(key)
            for key in self.CONTEXT_KEYS
            if need.get(key) not in (None, [], "")
        }
