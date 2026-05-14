"""Intent detection service."""

from __future__ import annotations

import re
from typing import Any

from app.schemas.chat import StructuredNeed


class IntentService:
    CATEGORY_KEYWORDS = {
        "\u673a\u68b0\u952e\u76d8": [
            "\u673a\u68b0\u952e\u76d8",
            "\u952e\u76d8",
        ],
        "\u84dd\u7259\u8033\u673a": [
            "\u84dd\u7259\u8033\u673a",
            "\u8033\u673a",
            "\u8033\u9ea6",
        ],
        "\u53f0\u706f": [
            "\u53f0\u706f",
            "\u62a4\u773c\u706f",
            "\u706f",
        ],
        "\u5145\u7535\u5b9d": [
            "\u5145\u7535\u5b9d",
            "\u79fb\u52a8\u7535\u6e90",
        ],
        "\u53cc\u80a9\u5305": [
            "\u53cc\u80a9\u5305",
            "\u80cc\u5305",
            "\u5305",
        ],
    }
    SCENARIO_KEYWORDS = [
        "\u5bbf\u820d",
        "\u529e\u516c",
        "\u901a\u52e4",
        "\u8fd0\u52a8",
        "\u5b66\u4e60",
        "\u5199\u4ee3\u7801",
    ]
    PREFERENCE_KEYWORDS = [
        "\u4f4e\u566a\u97f3",
        "\u65e0\u7ebf",
        "\u964d\u566a",
        "\u62a4\u773c",
        "\u8f7b\u4fbf",
        "\u5927\u5bb9\u91cf",
        "\u6027\u4ef7\u6bd4",
    ]
    BUDGET_PATTERNS = [
        re.compile(
            r"(?:\u9884\u7b97|\u4e0d\u8d85\u8fc7|\u4e0d\u8d85|"
            r"\u63a7\u5236\u5728|\u4f4e\u4e8e|\u5c11\u4e8e)"
            r"\s*(\d+(?:\.\d+)?)\s*(?:\u5143|\u5757)?"
        ),
        re.compile(
            r"(\d+(?:\.\d+)?)\s*(?:\u5143|\u5757)?\s*"
            r"(?:\u4ee5\u5185|\u4ee5\u4e0b|\u4e4b\u5185)"
        ),
    ]

    async def extract(
        self,
        text: str,
        image_info: dict | None = None,
        history_context: dict | None = None,
    ) -> StructuredNeed:
        normalized_text = text or ""
        image_info = image_info or {}
        history_context = history_context or {}

        # Future hook: call an LLM JSON extractor here, then merge/validate
        # against the rule-based result below.
        _ = self._build_llm_prompt(normalized_text, image_info, history_context)

        intent = self._extract_intent(normalized_text)
        category = (
            self._extract_category(normalized_text)
            or image_info.get("category")
            or history_context.get("category")
        )
        budget_max = self._extract_budget(normalized_text)
        if budget_max is None:
            budget_max = history_context.get("budget_max")

        scenario = self._extract_scenario(normalized_text) or history_context.get("scenario")
        preferences = self._extract_preferences(normalized_text)
        preferences.extend(self._coerce_list(image_info.get("features")))
        preferences.extend(self._coerce_list(history_context.get("preferences")))
        preferences = self._dedupe(preferences)

        missing_fields = self._missing_fields(
            intent=intent,
            category=category,
            budget_max=budget_max,
            scenario=scenario,
            preferences=preferences,
        )

        return StructuredNeed(
            intent=intent,
            category=category,
            budget_max=budget_max,
            scenario=scenario,
            preferences=preferences,
            need_clarify=bool(missing_fields),
            missing_fields=missing_fields,
        )

    def _extract_intent(self, text: str) -> str:
        if any(
            keyword in text
            for keyword in [
                "\u5bf9\u6bd4",
                "\u6bd4\u8f83",
                "\u54ea\u4e2a\u597d",
                "\u54ea\u6b3e\u597d",
            ]
        ):
            return "\u5546\u54c1\u5bf9\u6bd4"
        if any(
            keyword in text
            for keyword in [
                "\u5e73\u66ff",
                "\u66ff\u4ee3",
                "\u7c7b\u4f3c\u6b3e",
            ]
        ):
            return "\u627e\u5e73\u66ff"
        if any(
            keyword in text
            for keyword in [
                "\u503c\u4e0d\u503c",
                "\u5212\u7b97",
                "\u4ef7\u683c",
                "\u8d35\u4e0d\u8d35",
            ]
        ):
            return "\u4ef7\u683c\u5224\u65ad"
        if any(
            keyword in text
            for keyword in [
                "\u53c2\u6570",
                "\u89c4\u683c",
                "\u600e\u4e48\u9009",
                "\u914d\u7f6e",
            ]
        ):
            return "\u53c2\u6570\u54a8\u8be2"
        return "\u5546\u54c1\u63a8\u8350"

    def _extract_category(self, text: str) -> str | None:
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return category
        return None

    def _extract_budget(self, text: str) -> float | None:
        for pattern in self.BUDGET_PATTERNS:
            match = pattern.search(text)
            if match:
                value = float(match.group(1))
                return int(value) if value.is_integer() else value
        return None

    def _extract_scenario(self, text: str) -> str | None:
        for scenario in self.SCENARIO_KEYWORDS:
            if scenario in text:
                return scenario
        return None

    def _extract_preferences(self, text: str) -> list[str]:
        preferences = []
        for preference in self.PREFERENCE_KEYWORDS:
            if preference in text:
                preferences.append(preference)

        quiet_preference = "\u4f4e\u566a\u97f3"
        quiet_keywords = [
            "\u9759\u97f3",
            "\u58f0\u97f3\u5c0f",
            "\u5b89\u9759",
        ]
        if any(keyword in text for keyword in quiet_keywords):
            if quiet_preference not in preferences:
                preferences.append(quiet_preference)
        return preferences

    def _missing_fields(
        self,
        intent: str,
        category: str | None,
        budget_max: float | None,
        scenario: str | None,
        preferences: list[str],
    ) -> list[str]:
        if intent not in {"\u5546\u54c1\u63a8\u8350", "\u627e\u5e73\u66ff"}:
            return []

        missing_fields = []
        if category is None:
            missing_fields.append("category")
        if budget_max is None:
            missing_fields.append("budget_max")
        if scenario is None:
            missing_fields.append("scenario")
        if not preferences:
            missing_fields.append("preferences")
        return missing_fields

    def _coerce_list(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return [str(item) for item in value if item]
        return [str(value)]

    def _dedupe(self, values: list[str]) -> list[str]:
        result = []
        seen = set()
        for value in values:
            if value not in seen:
                result.append(value)
                seen.add(value)
        return result

    def _build_llm_prompt(
        self,
        text: str,
        image_info: dict,
        history_context: dict,
    ) -> str:
        return (
            "Extract shopping intent as JSON with fields: intent, category, "
            "budget_max, scenario, preferences, avoid, need_clarify, "
            f"missing_fields. text={text!r}, image_info={image_info!r}, "
            f"history_context={history_context!r}"
        )
