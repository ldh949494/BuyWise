"""Bundle recommendation assembly."""

from __future__ import annotations

from typing import Any

from app.schemas.chat import (
    BundleBudgetAllocation,
    BundleCompatibilityCheck,
    BundleCompleteness,
    BundlePlan,
    BundlePlanItem,
    ProductCard,
)
from app.services.bundle_templates import (
    DESKTOP_TEMPLATE as BUNDLE_DESKTOP_TEMPLATE,
    GENERAL_TEMPLATE as BUNDLE_GENERAL_TEMPLATE,
    TRAVEL_TEMPLATE as BUNDLE_TRAVEL_TEMPLATE,
    ScenarioTemplate,
)
from app.services.recommend_service import RecommendService


class BundleRecommendService:
    DESKTOP_TEMPLATE = BUNDLE_DESKTOP_TEMPLATE
    TRAVEL_TEMPLATE = BUNDLE_TRAVEL_TEMPLATE
    GENERAL_TEMPLATE = BUNDLE_GENERAL_TEMPLATE
    TIER_CONFIGS = [
        ("entry", "方案一 · 入门档", 0.72, "够用、省预算，优先配齐核心品类。"),
        ("balanced", "方案二 · 均衡档", 1.0, "核心体验和长期使用更均衡。"),
        ("premium", "方案三 · 高配档", 1.32, "预算更高，优先换取品质和舒适度余量。"),
    ]

    def __init__(self, recommend_service: RecommendService | None = None) -> None:
        self.recommend_service = recommend_service or RecommendService()

    def rank(self, products: list[Any], need: Any) -> list[Any]:
        return self.rank_cards(products, need)

    def build_plans(self, products: list[Any], need: Any) -> list[BundlePlan]:
        ranked_cards = self.recommend_service.rank(products, need)
        if not ranked_cards:
            return []
        category_cards = self._cards_by_category(ranked_cards, products)
        template = self._template_for_need(need, category_cards)
        budget_max = self._optional_float(self._get_value(need, "budget_max"))
        target_budget = budget_max or self._sum_reasonable_baseline(category_cards, template)
        return [
            plan
            for tier_index, tier_config in enumerate(self.TIER_CONFIGS, start=1)
            if (plan := self._build_plan(category_cards, need, template, target_budget, tier_index, tier_config)) is not None
        ]

    def _build_plan(
        self,
        category_cards: dict[str, list[ProductCard]],
        need: Any,
        template: ScenarioTemplate,
        target_budget: float,
        tier_index: int,
        tier_config: tuple[str, str, float, str],
    ) -> BundlePlan | None:
        tier, title, multiplier, summary = tier_config
        tier_budget = round(target_budget * multiplier, 2)
        items = self._build_plan_items(category_cards, tier_budget, tier_index, need, template)
        if not items:
            return None
        total_price = round(sum(item.product.price for item in items if not item.excluded), 2)
        budget_status = self._budget_status(total_price, tier_budget, need)
        title = title.replace("· ", f"· {template.title_prefix}")
        return self._plan_from_parts(tier, title, summary, tier_budget, total_price, budget_status, items, need, template)

    def _plan_from_parts(
        self,
        tier: str,
        title: str,
        summary: str,
        tier_budget: float,
        total_price: float,
        budget_status: str,
        items: list[BundlePlanItem],
        need: Any,
        template: ScenarioTemplate,
    ) -> BundlePlan:
        return BundlePlan(
            **self._plan_core(tier, title, summary, tier_budget, total_price, budget_status, items, need, template),
            **self._plan_details(tier, total_price, tier_budget, budget_status, items, template),
        )

    def _plan_core(
        self,
        tier: str,
        title: str,
        summary: str,
        tier_budget: float,
        total_price: float,
        budget_status: str,
        items: list[BundlePlanItem],
        need: Any,
        template: ScenarioTemplate,
    ) -> dict[str, Any]:
        return {
            "id": f"{template.key}-{tier}-{int(tier_budget)}",
            "title": title,
            "budget_tier": tier,
            "target_budget": tier_budget,
            "total_price": total_price,
            "budget_status": budget_status,
            "budget_delta": round(total_price - tier_budget, 2),
            "recommendation_level": "high" if tier == "balanced" else "medium",
            "scenario_fit": self._scenario_fit(need, template),
            "summary": self._summary_with_preferences(summary, need),
            "completeness": self._completeness(items, template),
            "budget_allocation": self._budget_allocation(items),
            "items": items,
            "revision": 1,
        }

    def _plan_details(
        self,
        tier: str,
        total_price: float,
        tier_budget: float,
        budget_status: str,
        items: list[BundlePlanItem],
        template: ScenarioTemplate,
    ) -> dict[str, Any]:
        return {
            "tradeoffs": self._tradeoffs(tier, total_price, tier_budget, budget_status, template),
            "compare_highlights": self._compare_highlights(tier, template),
            "exclusion_notes": self._exclusion_notes(items, template),
            "compatibility_checks": self._compatibility_checks(items, template),
            "availability_status": self._availability_status(items),
        }

    def _budget_allocation(self, items: list[BundlePlanItem]) -> list[BundleBudgetAllocation]:
        return [BundleBudgetAllocation(category=item.category, amount=item.product.price) for item in items]

    def rank_cards(self, products: list[Any], need: Any) -> list[Any]:
        ranked_cards = self.recommend_service.rank(products, need)
        category_by_id = {product.id: getattr(product, "category", None) for product in products}
        return self._select_bundle_cards(ranked_cards, category_by_id, self._get_value(need, "budget_max"))

    def _cards_by_category(self, cards: list[ProductCard], products: list[Any]) -> dict[str, list[ProductCard]]:
        category_by_id = {product.id: getattr(product, "category", None) for product in products}
        grouped: dict[str, list[ProductCard]] = {}
        for card in cards:
            category = category_by_id.get(card.id) or self._category_from_name(card.name)
            if not category:
                continue
            grouped.setdefault(category, []).append(card)
        for category_cards in grouped.values():
            category_cards.sort(key=lambda card: (card.price, -(card.score or 0)))
        return grouped

    def _build_plan_items(
        self,
        category_cards: dict[str, list[ProductCard]],
        tier_budget: float,
        tier_index: int,
        need: Any,
        template: ScenarioTemplate,
    ) -> list[BundlePlanItem]:
        owned_categories = set(self._string_list(self._get_value(need, "owned_categories")))
        excluded_categories = set(self._string_list(self._get_value(need, "excluded_categories")))
        items = self._required_plan_items(category_cards, tier_budget, tier_index, template, owned_categories, excluded_categories)
        remaining_budget = tier_budget - sum(item.product.price for item in items)
        items.extend(self._optional_plan_items(category_cards, remaining_budget, tier_budget, tier_index, template, excluded_categories))
        return items

    def _required_plan_items(
        self,
        category_cards: dict[str, list[ProductCard]],
        tier_budget: float,
        tier_index: int,
        template: ScenarioTemplate,
        owned_categories: set[str],
        excluded_categories: set[str],
    ) -> list[BundlePlanItem]:
        items = []
        for category in template.required_categories:
            if category in excluded_categories or self._is_owned_category(category, owned_categories):
                continue
            category_budget = tier_budget * template.budget_weights.get(category, 0.1)
            card = self._pick_card(category_cards.get(category, []), category_budget, tier_index)
            if card is not None:
                items.append(BundlePlanItem(category=category, product=card, role=self._role_for(category, template), required=True))
        return items

    def _optional_plan_items(
        self,
        category_cards: dict[str, list[ProductCard]],
        remaining_budget: float,
        tier_budget: float,
        tier_index: int,
        template: ScenarioTemplate,
        excluded_categories: set[str],
    ) -> list[BundlePlanItem]:
        items = []
        for category in template.optional_categories:
            if category in excluded_categories:
                continue
            category_budget = min(remaining_budget, tier_budget * template.optional_budget_weights.get(category, 0.03))
            card = self._pick_card(category_cards.get(category, []), max(category_budget, 0), max(tier_index - 1, 1))
            if card is None:
                continue
            if remaining_budget < card.price:
                continue
            items.append(BundlePlanItem(category=category, product=card, role=self._role_for(category, template), required=False))
            remaining_budget -= card.price
        return items

    def _pick_card(self, cards: list[ProductCard], category_budget: float, tier_index: int) -> ProductCard | None:
        if not cards:
            return None
        within_budget = [card for card in cards if card.price <= max(category_budget, 0) * 1.1]
        candidates = within_budget or cards
        index = min(max(tier_index - 1, 0), len(candidates) - 1)
        return candidates[index]

    def _completeness(self, items: list[BundlePlanItem], template: ScenarioTemplate) -> BundleCompleteness:
        included_required = len({item.category for item in items if item.required})
        missing = [category for category in template.required_categories if category not in {item.category for item in items}]
        needs_confirmation = [template.confirmation_prompts[category] for category in missing if category in template.confirmation_prompts]
        return BundleCompleteness(
            included_required=included_required,
            expected_required=len(template.required_categories),
            optional_included=len([item for item in items if not item.required]),
            missing=missing,
            needs_confirmation=needs_confirmation,
        )

    def _budget_status(self, total_price: float, target_budget: float, need: Any | None = None) -> str:
        if total_price <= target_budget:
            return "within_budget"
        flex_rate = self._optional_float(self._get_value(need, "budget_flex_rate")) if need is not None else None
        if total_price <= target_budget * (1 + (flex_rate if flex_rate is not None else 0.1)):
            return "slightly_over_budget"
        return "over_budget"

    def _tradeoffs(
        self,
        tier: str,
        total_price: float,
        target_budget: float,
        budget_status: str,
        template: ScenarioTemplate,
    ) -> list[str]:
        tradeoffs = {
            "entry": f"优先压低总价，先覆盖{template.title_prefix}核心品类。",
            "balanced": f"比入门档更重视{template.title_prefix}场景的完整度和稳定性。",
            "premium": f"预算更高，优先换取{template.title_prefix}场景的品质余量。",
        }
        result = [tradeoffs.get(tier, "按当前预算平衡核心品类。")]
        if budget_status == "slightly_over_budget":
            result.append(f"当前小幅超预算 {round(total_price - target_budget, 2)} 元，原因是优先保留核心品类。")
        elif budget_status == "over_budget":
            result.append(f"当前超预算 {round(total_price - target_budget, 2)} 元，建议替换高价单品。")
        return result

    def _compare_highlights(self, tier: str, template: ScenarioTemplate) -> list[str]:
        highlights = {
            "entry": [f"适合先配齐{template.title_prefix}核心清单，后续再升级。"],
            "balanced": [f"多花的钱主要换来更完整的{template.title_prefix}体验。"],
            "premium": [f"适合对{template.title_prefix}体验和品质余量要求更高的用户。"],
        }
        return highlights.get(tier, [])

    def _exclusion_notes(self, items: list[BundlePlanItem], template: ScenarioTemplate) -> list[str]:
        categories = {item.category for item in items}
        notes = []
        if template.key == "desktop" and "音箱" not in categories:
            notes.append("音箱未纳入：耳机已覆盖会议、网课和轻度娱乐。")
        if template.key == "desktop" and "摄像头" not in categories:
            notes.append("摄像头未纳入：仅在频繁视频会议时建议补充。")
        if template.key == "travel" and "防晒" not in categories:
            notes.append("防晒未纳入：当前商品池缺少对应商品，需单独补齐。")
        if template.key == "travel" and "鞋履" not in categories:
            notes.append("鞋履未纳入：建议按行程步行强度另行确认。")
        return notes[:2]

    def _summary_with_preferences(self, summary: str, need: Any) -> str:
        owned_categories = self._string_list(self._get_value(need, "owned_categories"))
        if not owned_categories:
            return summary
        return f"{summary} 已按偏好跳过已有品类：{'、'.join(owned_categories[:3])}。"

    def _compatibility_checks(self, items: list[BundlePlanItem], template: ScenarioTemplate) -> list[BundleCompatibilityCheck]:
        categories = {item.category for item in items}
        checks = []
        if template.key == "desktop" and {"电脑", "显示器"}.issubset(categories):
            checks.append(BundleCompatibilityCheck(title="显示连接", status="needs_confirmation", message="购买前确认电脑接口与显示器线材匹配。"))
        if template.key == "desktop" and {"显示器", "支架"}.issubset(categories):
            checks.append(BundleCompatibilityCheck(title="桌面空间", status="needs_confirmation", message="显示器和支架需要确认桌面深度。"))
        if template.key == "travel" and {"外套", "上衣"}.issubset(categories):
            checks.append(BundleCompatibilityCheck(title="穿搭层次", status="needs_confirmation", message="确认目的地昼夜温差和外套厚度是否匹配。"))
        if template.key == "travel" and "防晒" not in categories:
            checks.append(BundleCompatibilityCheck(title="防晒完整度", status="needs_confirmation", message="商品池缺少防晒品类，需要外部补齐。"))
        if not checks:
            checks.append(BundleCompatibilityCheck(title="搭配风险", status="pass", message="核心品类之间暂无明显搭配冲突。"))
        return checks

    def _availability_status(self, items: list[BundlePlanItem]) -> str:
        if any(item.product.conflicts for item in items):
            return "partially_available"
        return "available"

    def _role_for(self, category: str, template: ScenarioTemplate) -> str:
        return template.roles.get(category, "方案补充")

    def _scenario_fit(self, need: Any, template: ScenarioTemplate) -> str:
        scenario = self._get_value(need, "scenario")
        location = self._get_value(need, "location")
        if scenario:
            prefix = f"{location}{scenario}" if location else str(scenario)
            return f"{prefix}：{template.scenario_fit}"
        return template.scenario_fit

    def _sum_reasonable_baseline(self, category_cards: dict[str, list[ProductCard]], template: ScenarioTemplate) -> float:
        total = 0.0
        for category in template.required_categories:
            cards = category_cards.get(category, [])
            if cards:
                total += cards[0].price
        return total or template.default_budget

    def _category_from_name(self, name: str) -> str | None:
        for category in self._all_template_categories():
            if category in name:
                return category
        if "主机" in name or "笔记本" in name:
            return "电脑"
        return None

    def _template_for_need(self, need: Any, category_cards: dict[str, list[ProductCard]]) -> ScenarioTemplate:
        explicit = self._explicit_template(need, category_cards)
        if explicit is not None:
            return explicit
        scenario_text = " ".join(
            str(value or "")
            for value in [
                self._get_value(need, "scenario"),
                self._get_value(need, "location"),
                " ".join(self._string_list(self._get_value(need, "preferences"))),
            ]
        )
        if any(keyword in scenario_text for keyword in ["桌面", "办公", "编程", "宿舍"]):
            return self.DESKTOP_TEMPLATE
        if any(keyword in scenario_text for keyword in ["旅行", "出行", "度假", "三亚", "海边", "穿搭"]):
            return self.TRAVEL_TEMPLATE
        return self._generic_template(category_cards)

    def _explicit_template(self, need: Any, category_cards: dict[str, list[ProductCard]]) -> ScenarioTemplate | None:
        required = self._string_list(self._get_value(need, "must_have_categories"))
        if not required:
            return None
        optional = [category for category in category_cards if category not in required]
        weight = round(1 / max(len(required), 1), 3)
        return ScenarioTemplate(
            key="custom",
            title_prefix="定制",
            required_categories=required,
            optional_categories=optional[:5],
            budget_weights={category: weight for category in required},
            roles={category: "核心品类" for category in required},
            scenario_fit="按用户明确点名的品类组合",
            default_budget=self.GENERAL_TEMPLATE.default_budget,
        )

    def _generic_template(self, category_cards: dict[str, list[ProductCard]]) -> ScenarioTemplate:
        categories = list(category_cards.keys())
        required = categories[: min(5, len(categories))]
        optional = categories[len(required) : len(required) + 5]
        weight = round(1 / max(len(required), 1), 3)
        return ScenarioTemplate(
            key="general",
            title_prefix="场景",
            required_categories=required,
            optional_categories=optional,
            budget_weights={category: weight for category in required},
            roles={category: "核心品类" for category in required},
            scenario_fit=self.GENERAL_TEMPLATE.scenario_fit,
            default_budget=self.GENERAL_TEMPLATE.default_budget,
        )

    def _all_template_categories(self) -> list[str]:
        templates = [self.DESKTOP_TEMPLATE, self.TRAVEL_TEMPLATE]
        categories: list[str] = []
        for template in templates:
            categories.extend(template.required_categories)
            categories.extend(template.optional_categories)
        return categories

    def _select_bundle_cards(
        self,
        cards: list[Any],
        category_by_id: dict[int, str | None],
        budget_max: Any,
    ) -> list[Any]:
        selected = []
        selected_categories = set()
        total_price = 0.0
        for card in cards:
            category = category_by_id.get(card.id)
            if category in selected_categories:
                continue
            if budget_max is not None and selected and total_price + float(card.price) > float(budget_max):
                continue
            selected.append(card)
            if category:
                selected_categories.add(category)
            total_price += float(card.price)
            if len(selected) >= 5:
                break
        return selected or cards[:5]

    def _get_value(self, source: Any, key: str) -> Any:
        if source is None:
            return None
        if isinstance(source, dict):
            return source.get(key)
        return getattr(source, key, None)

    def _string_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]

    def _is_owned_category(self, category: str, owned_categories: set[str]) -> bool:
        if category in owned_categories:
            return True
        aliases = {
            "电脑": {"电脑", "主机", "笔记本"},
            "显示器": {"显示器", "屏幕"},
            "机械键盘": {"机械键盘", "键盘"},
            "鼠标": {"鼠标"},
            "蓝牙耳机": {"蓝牙耳机", "耳机"},
            "双肩包": {"双肩包", "背包", "包"},
            "防晒": {"防晒", "防晒霜", "遮阳"},
            "外套": {"外套", "夹克"},
            "上衣": {"上衣", "T恤", "衬衫"},
            "裤装": {"裤装", "裤子", "短裤"},
            "鞋履": {"鞋履", "鞋", "凉鞋", "拖鞋"},
        }.get(category, {category})
        return bool(aliases & owned_categories)

    def _optional_float(self, value: Any) -> float | None:
        if value in (None, ""):
            return None
        return float(value)
