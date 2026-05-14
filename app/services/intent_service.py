"""Intent detection service."""

from __future__ import annotations

import re
from typing import Any

from app.schemas.chat import StructuredNeed


class IntentService:
    CATEGORY_KEYWORDS = {
        "机械键盘": ["机械键盘", "键盘"],
        "蓝牙耳机": ["蓝牙耳机", "耳机", "耳麦"],
        "台灯": ["台灯", "护眼灯", "灯"],
        "充电宝": ["充电宝", "移动电源"],
        "双肩包": ["双肩包", "背包", "包"],
    }
    SCENARIO_KEYWORDS = ["宿舍", "办公", "通勤", "运动", "学习", "写代码"]
    PREFERENCE_KEYWORDS = ["低噪音", "无线", "降噪", "护眼", "轻便", "大容量", "性价比"]
    BUDGET_PATTERNS = [
        re.compile(r"(?:预算|不超过|不超|控制在|低于|少于)\s*(\d+(?:\.\d+)?)\s*(?:元|块)?"),
        re.compile(r"(\d+(?:\.\d+)?)\s*(?:元|块)?\s*(?:以内|以下|之内)"),
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
        if any(keyword in text for keyword in ["对比", "比较", "哪个好", "哪款好"]):
            return "商品对比"
        if any(keyword in text for keyword in ["平替", "替代", "类似款"]):
            return "找平替"
        if any(keyword in text for keyword in ["值不值", "划算", "价格", "贵不贵"]):
            return "价格判断"
        if any(keyword in text for keyword in ["参数", "规格", "怎么选", "配置"]):
            return "参数咨询"
        return "商品推荐"

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
        if "静音" in text and "低噪音" not in preferences:
            preferences.append("低噪音")
        return preferences

    def _missing_fields(
        self,
        intent: str,
        category: str | None,
        budget_max: float | None,
        scenario: str | None,
        preferences: list[str],
    ) -> list[str]:
        if intent not in {"商品推荐", "找平替"}:
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
