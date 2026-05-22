"""LLM-backed intent extraction helpers."""

from __future__ import annotations

import json
from typing import Any, Callable

from app.schemas.chat import StructuredNeed
from app.utils.list_values import dedupe_strings


MissingFieldsFn = Callable[[str, str | None, float | None, str | None, list[str]], list[str]]

CORE_MISSING_FIELDS = {"category", "budget_max", "scenario", "preferences"}
INTENT_ALIASES = {
    "推荐": "商品推荐",
    "商品推荐": "商品推荐",
    "找推荐": "商品推荐",
    "对比": "商品对比",
    "比较": "商品对比",
    "商品对比": "商品对比",
    "平替": "找平替",
    "找平替": "找平替",
    "价格判断": "价格判断",
    "参数咨询": "参数咨询",
}
CATEGORY_KEYWORDS = {
    "机械键盘": ["机械键盘", "键盘"],
    "蓝牙耳机": ["蓝牙耳机", "耳机", "耳麦"],
    "台灯": ["台灯", "护眼灯", "灯"],
    "充电宝": ["充电宝", "移动电源"],
    "双肩包": ["双肩包", "背包", "包"],
}
SCENARIO_KEYWORDS = ["宿舍", "办公", "通勤", "运动", "学习", "写代码", "旅行", "阅读", "应急"]
PREFERENCE_ALIASES = {
    "静音": "低噪音",
    "声音小": "低噪音",
    "安静": "低噪音",
    "性价比高": "性价比",
    "蓝牙": "无线",
    "主动降噪": "降噪",
}


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
        except (json.JSONDecodeError, KeyError, RuntimeError, TypeError, ValueError):
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
                    "avoid, need_clarify, missing_fields. Use Chinese values when the "
                    "user speaks Chinese. Do not invent product names."
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
        missing_fields = self.missing_fields(
            values["intent"],
            values["category"],
            values["budget_max"],
            values["scenario"],
            values["preferences"],
        )
        supplied_missing = [
            field
            for field in self._text_list(payload.get("missing_fields"))
            if field in CORE_MISSING_FIELDS
        ]
        if supplied_missing:
            missing_fields = dedupe_strings(missing_fields + supplied_missing)
        return StructuredNeed(
            intent=values["intent"],
            category=values["category"],
            budget_max=values["budget_max"],
            scenario=values["scenario"],
            preferences=values["preferences"],
            avoid=values["avoid"],
            need_clarify=bool(missing_fields),
            missing_fields=missing_fields,
        )

    def _payload_values(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "intent": self._normalize_intent(payload.get("intent")),
            "category": self._normalize_category(payload.get("category")),
            "budget_max": self._optional_float(payload.get("budget_max")),
            "scenario": self._normalize_scenario(payload.get("scenario")),
            "preferences": self._normalize_preferences(payload.get("preferences")),
            "avoid": dedupe_strings(self._text_list(payload.get("avoid"))),
        }

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

    def _prompt(self, text: str, image_info: dict, history_context: dict) -> str:
        return (
            "Extract shopping intent as JSON with fields: intent, category, "
            "budget_max, scenario, preferences, avoid, need_clarify, "
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

    def _optional_float(self, value: Any) -> float | None:
        if value in (None, ""):
            return None
        number = float(value)
        return int(number) if number.is_integer() else number
