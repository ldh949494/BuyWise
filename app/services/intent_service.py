"""Intent detection service."""

from __future__ import annotations

import re
from typing import Any

from app.schemas.chat import StructuredNeed
from app.services.intent_llm import LlmIntentExtractor
from app.utils.intent_strategy import retrieval_strategy_for
from app.utils.list_values import dedupe_strings


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
        "\u7535\u8111": [
            "\u7535\u8111",
            "\u4e3b\u673a",
            "\u7b14\u8bb0\u672c",
            "\u8ff7\u4f60\u4e3b\u673a",
        ],
        "\u663e\u793a\u5668": [
            "\u663e\u793a\u5668",
            "\u5c4f\u5e55",
            "\u663e\u793a\u5c4f",
        ],
        "\u9f20\u6807": [
            "\u9f20\u6807",
        ],
        "\u652f\u67b6": [
            "\u652f\u67b6",
            "\u663e\u793a\u5668\u652f\u67b6",
        ],
        "\u62d3\u5c55\u575e": [
            "\u62d3\u5c55\u575e",
            "\u6269\u5c55\u575e",
            "\u6269\u5c55\u575e",
        ],
        "\u63d2\u6392": [
            "\u63d2\u6392",
            "\u6392\u63d2",
            "\u63d2\u7ebf\u677f",
        ],
        "\u9632\u6652": ["\u9632\u6652", "\u9632\u6652\u971c", "\u9632\u6652\u55b7\u96fe"],
        "\u5916\u5957": ["\u5916\u5957", "\u5939\u514b", "\u51b2\u950b\u8863"],
        "\u4e0a\u8863": ["\u4e0a\u8863", "T\u6064", "\u886c\u886b", "\u77ed\u8896"],
        "\u88e4\u88c5": ["\u88e4\u88c5", "\u88e4\u5b50", "\u77ed\u88e4", "\u957f\u88e4"],
        "\u978b\u5c65": ["\u978b", "\u978b\u5c65", "\u51c9\u978b", "\u62d6\u978b", "\u8fd0\u52a8\u978b"],
        "\u58a8\u955c": ["\u58a8\u955c", "\u592a\u9633\u955c"],
        "\u5e3d\u5b50": ["\u5e3d\u5b50", "\u906e\u9633\u5e3d"],
    }
    SCENARIO_KEYWORDS = [
        "\u5bbf\u820d",
        "\u529e\u516c",
        "\u901a\u52e4",
        "\u8fd0\u52a8",
        "\u5b66\u4e60",
        "\u5199\u4ee3\u7801",
        "\u65c5\u884c",
        "\u5ea6\u5047",
        "\u9605\u8bfb",
        "\u5e94\u6025",
        "\u684c\u9762",
        "\u7535\u8111\u5916\u8bbe",
        "\u79df\u623f",
        "\u505a\u996d",
        "\u53a8\u623f",
        "\u6d77\u8fb9",
        "\u6237\u5916",
        "\u7a7f\u642d",
    ]
    PREFERENCE_KEYWORDS = [
        "\u4f4e\u566a\u97f3",
        "\u65e0\u7ebf",
        "\u964d\u566a",
        "\u62a4\u773c",
        "\u8f7b\u4fbf",
        "\u5927\u5bb9\u91cf",
        "\u6027\u4ef7\u6bd4",
        "\u5feb\u5145",
        "\u9632\u6cfc\u6c34",
        "\u5c0f\u5de7",
        "\u900f\u6c14",
        "\u901f\u5e72",
        "\u9632\u6652",
        "\u9ad8\u989c\u503c",
        "\u4f11\u95f2",
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
    BROWSE_KEYWORDS = ["随便看看", "先看看", "看看", "逛逛", "了解一下", "有什么", "推荐几类"]
    BUY_READY_KEYWORDS = ["想买", "准备买", "马上买", "下单", "入手", "就买", "要买"]
    SHOPPING_TARGET_KEYWORDS = [
        "空气炸锅",
        "电煮锅",
        "吸尘器",
        "清洁机",
        "智能手表",
        "手表",
        "投影仪",
        "咖啡杯",
        "保温杯",
        "学习平板",
        "平板",
        "电脑包",
        "数码配件",
        "小家电",
    ]

    def __init__(self, llm_client: Any | None = None) -> None:
        self.llm_client = llm_client

    async def extract(
        self,
        text: str,
        image_info: dict | None = None,
        history_context: dict | None = None,
    ) -> StructuredNeed:
        normalized_text = text or ""
        image_info = image_info or {}
        history_context = history_context or {}

        rule_need = self._extract_by_rules(normalized_text, image_info, history_context)
        if self.llm_client is None:
            return rule_need

        extractor = LlmIntentExtractor(self.llm_client, self._missing_fields)
        llm_need = await extractor.extract(normalized_text, image_info, history_context)
        return self._prefer_need(rule_need, llm_need)

    def extract_by_rules(
        self,
        text: str,
        image_info: dict | None = None,
        history_context: dict | None = None,
    ) -> StructuredNeed:
        return self._extract_by_rules(text or "", image_info or {}, history_context or {})

    def _extract_by_rules(
        self,
        normalized_text: str,
        image_info: dict,
        history_context: dict,
    ) -> StructuredNeed:
        values = self._rule_values(normalized_text, image_info, history_context)
        missing_fields = self._missing_fields(
            intent=values["intent"],
            category=values["category"],
            budget_max=values["budget_max"],
            scenario=values["scenario"],
            preferences=values["preferences"],
            purchase_stage=values["purchase_stage"],
        )
        return StructuredNeed(
            **values,
            need_clarify=bool(missing_fields),
            missing_fields=missing_fields,
        )

    def _rule_values(
        self,
        normalized_text: str,
        image_info: dict,
        history_context: dict,
    ) -> dict[str, Any]:
        intent = self._extract_intent(normalized_text)
        category = self._rule_category(intent, normalized_text, image_info, history_context)
        budget_max = self._rule_budget(normalized_text, history_context)
        scenario = self._extract_scenario(normalized_text) or history_context.get("scenario")
        preferences = self._rule_preferences(normalized_text, image_info, history_context)
        purchase_stage = self._purchase_stage(normalized_text, budget_max, scenario, preferences)
        return {
            "intent": intent,
            "category": category,
            "budget_max": budget_max,
            "scenario": scenario,
            "target_date": self._extract_target_date(normalized_text),
            "location": self._extract_location(normalized_text),
            "duration_days": self._extract_duration_days(normalized_text),
            "occasion": self._extract_occasion(normalized_text),
            "preferences": preferences,
            "avoid": self._extract_avoid(normalized_text),
            "style_preferences": self._extract_style_preferences(normalized_text),
            "must_have_categories": self._extract_must_have_categories(normalized_text) if intent == "bundle_recommend" else [],
            "excluded_categories": self._extract_excluded_categories(normalized_text),
            "purchase_stage": purchase_stage,
            "retrieval_strategy": retrieval_strategy_for(intent, purchase_stage),
        }

    def _rule_category(
        self,
        intent: str,
        normalized_text: str,
        image_info: dict,
        history_context: dict,
    ) -> str | None:
        if intent == "bundle_recommend":
            return None
        return (
            self._extract_category(normalized_text)
            or image_info.get("category")
            or history_context.get("category")
            or self._extract_shopping_target(normalized_text)
        )

    def _rule_budget(self, normalized_text: str, history_context: dict) -> float | None:
        budget_max = self._extract_budget(normalized_text)
        if budget_max is None:
            return history_context.get("budget_max")
        return budget_max

    def _rule_preferences(
        self,
        normalized_text: str,
        image_info: dict,
        history_context: dict,
    ) -> list[str]:
        preferences = self._extract_preferences(normalized_text)
        preferences.extend(self._coerce_list(image_info.get("features")))
        preferences.extend(self._coerce_list(history_context.get("preferences")))
        return dedupe_strings(preferences)

    def _extract_intent(self, text: str) -> str:
        if self._is_bundle_intent(text):
            return "bundle_recommend"
        if self._is_compare_intent(text):
            return "\u5546\u54c1\u5bf9\u6bd4"
        if self._is_alternative_intent(text):
            return "\u627e\u5e73\u66ff"
        if self._is_price_judgement_intent(text):
            return "\u4ef7\u683c\u5224\u65ad"
        if self._is_parameter_intent(text):
            return "\u53c2\u6570\u54a8\u8be2"
        return "\u5546\u54c1\u63a8\u8350"

    def _is_compare_intent(self, text: str) -> bool:
        return self._contains_keyword(text, ["\u5bf9\u6bd4", "\u6bd4\u8f83", "\u54ea\u4e2a\u597d", "\u54ea\u6b3e\u597d"])

    def _is_bundle_intent(self, text: str) -> bool:
        return self._contains_keyword(
            text,
            [
                "\u642d\u914d",
                "\u4e00\u5957",
                "\u5957\u88c5",
                "\u7ec4\u5408",
                "\u65b9\u6848",
                "\u6e05\u5355",
                "\u914d\u9f50",
                "\u5168\u5957",
                "\u684c\u9762\u88c5\u5907",
                "\u7535\u8111\u5916\u8bbe",
                "\u4ece",
                "\u7a7f\u642d",
            ],
        )

    def _is_alternative_intent(self, text: str) -> bool:
        return self._contains_keyword(text, ["\u5e73\u66ff", "\u66ff\u4ee3", "\u7c7b\u4f3c\u6b3e"])

    def _is_price_judgement_intent(self, text: str) -> bool:
        return self._contains_keyword(text, ["\u503c\u4e0d\u503c", "\u5212\u7b97", "\u4ef7\u683c", "\u8d35\u4e0d\u8d35"])

    def _is_parameter_intent(self, text: str) -> bool:
        return self._contains_keyword(text, ["\u53c2\u6570", "\u89c4\u683c", "\u600e\u4e48\u9009", "\u914d\u7f6e"])

    def _contains_keyword(self, text: str, keywords: list[str]) -> bool:
        return any(keyword in text for keyword in keywords)

    def _purchase_stage(
        self,
        text: str,
        budget_max: float | None,
        scenario: str | None,
        preferences: list[str],
    ) -> str:
        if self._contains_keyword(text, self.BROWSE_KEYWORDS):
            return "browse"
        if self._contains_keyword(text, self.BUY_READY_KEYWORDS):
            return "buy_ready"
        if budget_max is not None and (scenario is not None or preferences):
            return "buy_ready"
        return "consider"

    def _extract_category(self, text: str) -> str | None:
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return category
        return None

    def _extract_shopping_target(self, text: str) -> str | None:
        for target in self.SHOPPING_TARGET_KEYWORDS:
            if target in text:
                return target
        return None

    def _extract_must_have_categories(self, text: str) -> list[str]:
        categories = []
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                categories.append(category)
        if "\u7a7f\u642d" in text and not any(category in categories for category in ["\u4e0a\u8863", "\u88e4\u88c5", "\u978b\u5c65"]):
            categories.extend(["\u4e0a\u8863", "\u88e4\u88c5", "\u978b\u5c65"])
        return dedupe_strings(categories)

    def _extract_excluded_categories(self, text: str) -> list[str]:
        if not self._contains_keyword(text, ["\u4e0d\u8981", "\u4e0d\u9700\u8981", "\u6392\u9664", "\u53bb\u6389"]):
            return []
        return [
            category
            for category, keywords in self.CATEGORY_KEYWORDS.items()
            if any(self._contains_any_negative_context(text, keyword) for keyword in keywords)
        ]

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

    def _extract_location(self, text: str) -> str | None:
        match = re.search(r"(?:\u53bb|\u5230|\u5728)([\u4e00-\u9fa5A-Za-z]{2,16})(?:\u65c5\u884c|\u5ea6\u5047|\u51fa\u5dee|\u65c5\u6e38|\u73a9|\u7a7f\u642d|\u4e0b\u5468|\uff0c|,|\u3002|$)", text)
        if match:
            return match.group(1)
        return None

    def _extract_target_date(self, text: str) -> str | None:
        for marker in ["\u4eca\u5929", "\u660e\u5929", "\u5468\u672b", "\u4e0b\u5468", "\u8fd9\u4e2a\u6708", "\u56fd\u5e86", "\u6625\u8282"]:
            if marker in text:
                return marker
        match = re.search(r"(\d{1,2})\u6708(\d{1,2})\u65e5", text)
        if match:
            return f"{match.group(1)}\u6708{match.group(2)}\u65e5"
        return None

    def _extract_duration_days(self, text: str) -> int | None:
        match = re.search(r"(\d{1,2})\s*(?:\u5929|\u65e5)", text)
        if match:
            return int(match.group(1))
        return None

    def _extract_occasion(self, text: str) -> str | None:
        for occasion in ["\u5a5a\u793c", "\u9762\u8bd5", "\u901a\u52e4", "\u5ea6\u5047", "\u6d77\u8fb9", "\u9732\u8425", "\u5f92\u6b65", "\u4e0a\u8bfe", "\u7ea6\u4f1a"]:
            if occasion in text:
                return occasion
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

    def _extract_style_preferences(self, text: str) -> list[str]:
        styles = ["\u4f11\u95f2", "\u901a\u52e4", "\u8fd0\u52a8", "\u6781\u7b80", "\u65e5\u7cfb", "\u6237\u5916", "\u751c\u9177", "\u5546\u52a1", "\u9ad8\u989c\u503c", "\u8f7b\u719f"]
        return [style for style in styles if style in text]

    def _extract_avoid(self, text: str) -> list[str]:
        if not self._contains_keyword(text, ["\u4e0d\u8981", "\u4e0d\u60f3\u8981", "\u907f\u514d", "\u6392\u9664"]):
            return []
        return [
            preference
            for preference in self.PREFERENCE_KEYWORDS
            if self._contains_any_negative_context(text, preference)
        ]

    def _contains_any_negative_context(self, text: str, value: str) -> bool:
        return any(marker in text for marker in [f"\u4e0d\u8981{value}", f"\u4e0d\u60f3\u8981{value}", f"\u907f\u514d{value}", f"\u6392\u9664{value}"])

    def _missing_fields(
        self,
        intent: str,
        category: str | None,
        budget_max: float | None,
        scenario: str | None,
        preferences: list[str],
        purchase_stage: str = "consider",
    ) -> list[str]:
        if purchase_stage == "browse":
            return self._browse_missing_fields(category)

        if intent in {"bundle_recommend", "\u573a\u666f\u5316\u7ec4\u5408\u63a8\u8350"}:
            return self._bundle_missing_fields(scenario)

        if intent not in {"\u5546\u54c1\u63a8\u8350", "\u627e\u5e73\u66ff"}:
            return []

        return self._recommendation_missing_fields(category, budget_max, scenario, preferences)

    def _browse_missing_fields(self, category: str | None) -> list[str]:
        return ["category"] if category is None else []

    def _bundle_missing_fields(self, scenario: str | None) -> list[str]:
        return []

    def _recommendation_missing_fields(
        self,
        category: str | None,
        budget_max: float | None,
        scenario: str | None,
        preferences: list[str],
    ) -> list[str]:
        _ = budget_max, scenario, preferences
        if category is None:
            return ["category"]
        return []

    def _coerce_list(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value] if value.strip() else []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return [str(value).strip()] if str(value).strip() else []

    def _prefer_need(self, rule_need: StructuredNeed, llm_need: StructuredNeed | None) -> StructuredNeed:
        if llm_need is None:
            return rule_need
        if (
            llm_need.need_clarify
            and "category" in llm_need.missing_fields
            and not rule_need.need_clarify
        ):
            return rule_need
        return llm_need
