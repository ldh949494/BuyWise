"""LLM-backed intent extraction helpers."""

from __future__ import annotations

import json
from typing import Any, Callable

from app.core.providers import AppError
from app.schemas.chat import StructuredNeed
from app.services.intent_taxonomy import (
    CATEGORY_KEYWORDS,
    CORE_MISSING_FIELDS,
    INTENT_ALIASES,
    PREFERENCE_ALIASES,
    SCENARIO_KEYWORDS,
)
from app.utils.intent_strategy import retrieval_strategy_for
from app.utils.list_values import dedupe_strings


MissingFieldsFn = Callable[[str, str | None, float | None, str | None, list[str], str], list[str]]


class LlmIntentExtractor:
    def __init__(self, llm_client: Any, missing_fields: MissingFieldsFn) -> None:
        self.llm_client = llm_client
        self.missing_fields = missing_fields

    async def extract(
        self,
        text: str,
        image_info: dict,
        history_context: dict,
    ) -> StructuredNeed | None:
        try:
            content = await self.llm_client.chat(self._messages(text, image_info, history_context))
            payload = self._parse_json(content)
            if not isinstance(payload, dict):
                return None
            return self._need_from_payload(payload)
        except (AppError, json.JSONDecodeError, KeyError, RuntimeError, TypeError, ValueError):
            return None

    def _messages(
        self,
        text: str,
        image_info: dict,
        history_context: dict,
    ) -> list[dict[str, str]]:
        return [
            {
                "role": "system",
                "content": (
                    "You extract shopping intent for BuyWise. Return only strict JSON "
                    "with keys: intent, category, budget_max, scenario, preferences, "
                    "avoid, purchase_stage, retrieval_strategy, need_clarify, "
                    "missing_fields. purchase_stage must be browse, consider, or "
                    "buy_ready. retrieval_strategy must be explore, balanced, strict, "
                    "or bundle. Use bundle_recommend for bundle requests. "
                    "Do not invent product names."
                ),
            },
            {
                "role": "user",
                "content": self._prompt(text, image_info, history_context),
            },
        ]

    def _parse_json(self, content: str) -> Any:
        normalized = content.strip()
        if normalized.startswith("```"):
            normalized = self._strip_code_fence(normalized)
        return json.loads(normalized)

    def _strip_code_fence(self, content: str) -> str:
        lines = content.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()

    def _need_from_payload(self, payload: dict[str, Any]) -> StructuredNeed | None:
        values = self._payload_values(payload)
        if not values["intent"]:
            return None
        missing_fields = self._combined_missing_fields(values, payload)
        return self._build_need(values, missing_fields)

    def _combined_missing_fields(self, values: dict[str, Any], payload: dict[str, Any]) -> list[str]:
        missing_fields = self.missing_fields(
            values["intent"],
            values["category"],
            values["budget_max"],
            values["scenario"],
            values["preferences"],
            values["purchase_stage"],
        )
        supplied_missing = self._supplied_core_missing_fields(payload)
        return dedupe_strings(missing_fields + supplied_missing) if supplied_missing else missing_fields

    def _supplied_core_missing_fields(self, payload: dict[str, Any]) -> list[str]:
        return [field for field in self._text_list(payload.get("missing_fields")) if field in CORE_MISSING_FIELDS]

    def _build_need(self, values: dict[str, Any], missing_fields: list[str]) -> StructuredNeed:
        return StructuredNeed(
            intent=values["intent"],
            category=values["category"],
            budget_max=values["budget_max"],
            scenario=values["scenario"],
            target_date=values["target_date"],
            location=values["location"],
            duration_days=values["duration_days"],
            occasion=values["occasion"],
            preferences=values["preferences"],
            avoid=values["avoid"],
            style_preferences=values["style_preferences"],
            must_have_categories=values["must_have_categories"],
            excluded_categories=values["excluded_categories"],
            purchase_stage=values["purchase_stage"],
            retrieval_strategy=values["retrieval_strategy"],
            need_clarify=bool(missing_fields),
            missing_fields=missing_fields,
        )

    def _payload_values(self, payload: dict[str, Any]) -> dict[str, Any]:
        values = self._core_payload_values(payload)
        values.update(self._scenario_payload_values(payload))
        values.update(self._list_payload_values(payload))
        values["retrieval_strategy"] = self._payload_retrieval_strategy(payload, values["intent"], values["purchase_stage"])
        return values

    def _core_payload_values(self, payload: dict[str, Any]) -> dict[str, Any]:
        intent = self._normalize_intent(payload.get("intent"))
        budget_max = self._optional_float(payload.get("budget_max"))
        scenario = self._normalize_scenario(payload.get("scenario"))
        preferences = self._normalize_preferences(payload.get("preferences"))
        return {
            "intent": intent,
            "category": self._normalize_category(payload.get("category")),
            "budget_max": budget_max,
            "scenario": scenario,
            "preferences": preferences,
            "purchase_stage": self._normalize_purchase_stage(
                payload.get("purchase_stage"),
                budget_max=budget_max,
                scenario=scenario,
                preferences=preferences,
            ),
        }

    def _scenario_payload_values(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "target_date": self._optional_text(payload.get("target_date")),
            "location": self._optional_text(payload.get("location")),
            "duration_days": self._optional_int(payload.get("duration_days")),
            "occasion": self._optional_text(payload.get("occasion")),
        }

    def _list_payload_values(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "avoid": dedupe_strings(self._text_list(payload.get("avoid"))),
            "style_preferences": dedupe_strings(self._text_list(payload.get("style_preferences"))),
            "must_have_categories": dedupe_strings(self._text_list(payload.get("must_have_categories"))),
            "excluded_categories": dedupe_strings(self._text_list(payload.get("excluded_categories"))),
        }

    def _payload_retrieval_strategy(self, payload: dict[str, Any], intent: str, purchase_stage: str) -> str:
        retrieval_strategy = self._normalize_retrieval_strategy(payload.get("retrieval_strategy"))
        if payload.get("retrieval_strategy") in (None, ""):
            return retrieval_strategy_for(intent, purchase_stage)
        return retrieval_strategy

    def _normalize_intent(self, value: Any) -> str:
        intent = self._optional_text(value) or ""
        return INTENT_ALIASES.get(intent, intent)

    def _normalize_category(self, value: Any) -> str | None:
        category = self._optional_text(value)
        if category is None:
            return None
        for normalized, keywords in CATEGORY_KEYWORDS.items():
            if any(keyword in category for keyword in keywords):
                return normalized
        return category

    def _normalize_scenario(self, value: Any) -> str | None:
        scenario = self._optional_text(value)
        if scenario is None:
            return None
        for keyword in SCENARIO_KEYWORDS:
            if keyword in scenario:
                return keyword
        return scenario

    def _normalize_preferences(self, value: Any) -> list[str]:
        preferences = []
        for item in self._text_list(value):
            preferences.append(PREFERENCE_ALIASES.get(item, item))
        return dedupe_strings(preferences)

    def _normalize_purchase_stage(
        self,
        value: Any,
        *,
        budget_max: float | None,
        scenario: str | None,
        preferences: list[str],
    ) -> str:
        stage_text = self._optional_text(value)
        if stage_text is None:
            if budget_max is not None and (scenario is not None or preferences):
                return "buy_ready"
            return "consider"
        stage = stage_text.lower()
        aliases = {
            "explore": "browse",
            "浏览": "browse",
            "随便看看": "browse",
            "考虑": "consider",
            "明确购买": "buy_ready",
            "购买": "buy_ready",
            "ready": "buy_ready",
        }
        normalized = aliases.get(stage, stage)
        return normalized if normalized in {"browse", "consider", "buy_ready"} else "consider"

    def _normalize_retrieval_strategy(self, value: Any) -> str:
        strategy = (self._optional_text(value) or "balanced").lower()
        aliases = {
            "浏览": "explore",
            "探索": "explore",
            "精确": "strict",
            "严格": "strict",
            "组合": "bundle",
        }
        normalized = aliases.get(strategy, strategy)
        return normalized if normalized in {"explore", "balanced", "strict", "bundle"} else "balanced"

    def _prompt(self, text: str, image_info: dict, history_context: dict) -> str:
        return (
            "Extract shopping intent as JSON with fields: intent, category, "
            "budget_max, scenario, target_date, location, duration_days, "
            "occasion, preferences, avoid, style_preferences, "
            "must_have_categories, excluded_categories, purchase_stage, "
            "retrieval_strategy, need_clarify, "
            "Use intent bundle_recommend when the user asks for a bundle, kit, "
            "set, checklist, or cross-category scenario plan. "
            "Use purchase_stage=browse and retrieval_strategy=explore for casual "
            "browsing such as 随便看看 or 了解一下. Use purchase_stage=buy_ready "
            "and retrieval_strategy=strict when budget, scenario, or purchase wording "
            "shows a clear buying decision. "
            f"missing_fields. text={text!r}, image_info={image_info!r}, "
            f"history_context={history_context!r}"
        )

    def _text_list(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            normalized = value.strip()
            return [normalized] if normalized else []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        normalized = str(value).strip()
        return [normalized] if normalized else []

    def _optional_text(self, value: Any) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    def _optional_int(self, value: Any) -> int | None:
        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _optional_float(self, value: Any) -> float | None:
        if value in (None, ""):
            return None
        number = float(value)
        return int(number) if number.is_integer() else number
