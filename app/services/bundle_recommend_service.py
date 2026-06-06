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
from app.services.recommend_service import RecommendService


class BundleRecommendService:
    REQUIRED_DESKTOP_CATEGORIES = ["电脑", "显示器", "机械键盘", "鼠标", "蓝牙耳机"]
    SUPPORT_DESKTOP_CATEGORIES = ["台灯", "支架", "拓展坞", "插排"]
    REQUIRED_BUDGET_WEIGHTS = {
        "电脑": 0.55,
        "显示器": 0.22,
        "机械键盘": 0.07,
        "鼠标": 0.04,
        "蓝牙耳机": 0.08,
    }
    SUPPORT_BUDGET_WEIGHTS = {
        "台灯": 0.04,
        "支架": 0.03,
        "拓展坞": 0.04,
        "插排": 0.02,
    }
    TIER_CONFIGS = [
        ("entry", "方案一 · 入门桌面档", 0.72, "够用、省预算，优先配齐核心品类。"),
        ("balanced", "方案二 · 均衡桌面档", 1.0, "显示体验、输入体验和稳定性更均衡。"),
        ("premium", "方案三 · 高配桌面档", 1.32, "性能和舒适度余量更高，适合长期使用。"),
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
        budget_max = self._optional_float(self._get_value(need, "budget_max"))
        target_budget = budget_max or self._sum_reasonable_baseline(category_cards)
        return [
            plan
            for tier_index, tier_config in enumerate(self.TIER_CONFIGS, start=1)
            if (plan := self._build_plan(category_cards, need, target_budget, tier_index, tier_config)) is not None
        ]

    def _build_plan(
        self,
        category_cards: dict[str, list[ProductCard]],
        need: Any,
        target_budget: float,
        tier_index: int,
        tier_config: tuple[str, str, float, str],
    ) -> BundlePlan | None:
        tier, title, multiplier, summary = tier_config
        tier_budget = round(target_budget * multiplier, 2)
        items = self._build_plan_items(category_cards, tier_budget, tier_index, need)
        if not items:
            return None
        total_price = round(sum(item.product.price for item in items if not item.excluded), 2)
        budget_status = self._budget_status(total_price, tier_budget, need)
        return self._plan_from_parts(tier, title, summary, tier_budget, total_price, budget_status, items, need)

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
    ) -> BundlePlan:
        return BundlePlan(
            **self._plan_core(tier, title, summary, tier_budget, total_price, budget_status, items, need),
            **self._plan_details(tier, total_price, tier_budget, budget_status, items),
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
    ) -> dict[str, Any]:
        return {
            "id": f"desktop-{tier}-{int(tier_budget)}",
            "title": title,
            "budget_tier": tier,
            "target_budget": tier_budget,
            "total_price": total_price,
            "budget_status": budget_status,
            "budget_delta": round(total_price - tier_budget, 2),
            "recommendation_level": "high" if tier == "balanced" else "medium",
            "scenario_fit": self._scenario_fit(need),
            "summary": self._summary_with_preferences(summary, need),
            "completeness": self._completeness(items),
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
    ) -> dict[str, Any]:
        return {
            "tradeoffs": self._tradeoffs(tier, total_price, tier_budget, budget_status),
            "compare_highlights": self._compare_highlights(tier),
            "exclusion_notes": self._exclusion_notes(items),
            "compatibility_checks": self._compatibility_checks(items),
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
    ) -> list[BundlePlanItem]:
        items = []
        owned_categories = set(self._string_list(self._get_value(need, "owned_categories")))
        for category in self.REQUIRED_DESKTOP_CATEGORIES:
            if self._is_owned_category(category, owned_categories):
                continue
            category_budget = tier_budget * self.REQUIRED_BUDGET_WEIGHTS.get(category, 0.1)
            card = self._pick_card(category_cards.get(category, []), category_budget, tier_index)
            if card is None:
                continue
            items.append(BundlePlanItem(category=category, product=card, role=self._role_for(category), required=True))
        remaining_budget = tier_budget - sum(item.product.price for item in items)
        for category in self.SUPPORT_DESKTOP_CATEGORIES:
            category_budget = min(remaining_budget, tier_budget * self.SUPPORT_BUDGET_WEIGHTS.get(category, 0.03))
            card = self._pick_card(category_cards.get(category, []), max(category_budget, 0), max(tier_index - 1, 1))
            if card is None:
                continue
            if remaining_budget < card.price:
                continue
            items.append(BundlePlanItem(category=category, product=card, role=self._role_for(category), required=False))
            remaining_budget -= card.price
        return items

    def _pick_card(self, cards: list[ProductCard], category_budget: float, tier_index: int) -> ProductCard | None:
        if not cards:
            return None
        within_budget = [card for card in cards if card.price <= max(category_budget, 0) * 1.1]
        candidates = within_budget or cards
        index = min(max(tier_index - 1, 0), len(candidates) - 1)
        return candidates[index]

    def _completeness(self, items: list[BundlePlanItem]) -> BundleCompleteness:
        included_required = len({item.category for item in items if item.required})
        missing = [category for category in self.REQUIRED_DESKTOP_CATEGORIES if category not in {item.category for item in items}]
        needs_confirmation = []
        if "显示器" in missing:
            needs_confirmation.append("是否已有显示器")
        if "电脑" in missing:
            needs_confirmation.append("是否已有电脑或主机")
        return BundleCompleteness(
            included_required=included_required,
            expected_required=len(self.REQUIRED_DESKTOP_CATEGORIES),
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

    def _tradeoffs(self, tier: str, total_price: float, target_budget: float, budget_status: str) -> list[str]:
        tradeoffs = {
            "entry": "优先压低总价，可选配件会更克制。",
            "balanced": "比入门档更重视显示器、输入设备和长期稳定性。",
            "premium": "预算更高，优先换取性能余量、显示体验和舒适度。",
        }
        result = [tradeoffs.get(tier, "按当前预算平衡核心品类。")]
        if budget_status == "slightly_over_budget":
            result.append(f"当前小幅超预算 {round(total_price - target_budget, 2)} 元，原因是优先保留核心品类。")
        elif budget_status == "over_budget":
            result.append(f"当前超预算 {round(total_price - target_budget, 2)} 元，建议替换高价单品。")
        return result

    def _compare_highlights(self, tier: str) -> list[str]:
        highlights = {
            "entry": ["适合先配齐核心桌面，后续再升级配件。"],
            "balanced": ["多花的钱主要换来更稳的显示和输入体验。"],
            "premium": ["适合长期办公、编程和轻度游戏的高舒适度组合。"],
        }
        return highlights.get(tier, [])

    def _exclusion_notes(self, items: list[BundlePlanItem]) -> list[str]:
        categories = {item.category for item in items}
        notes = []
        if "音箱" not in categories:
            notes.append("音箱未纳入：耳机已覆盖会议、网课和轻度娱乐。")
        if "摄像头" not in categories:
            notes.append("摄像头未纳入：仅在频繁视频会议时建议补充。")
        return notes[:2]

    def _summary_with_preferences(self, summary: str, need: Any) -> str:
        owned_categories = self._string_list(self._get_value(need, "owned_categories"))
        if not owned_categories:
            return summary
        return f"{summary} 已按偏好跳过已有品类：{'、'.join(owned_categories[:3])}。"

    def _compatibility_checks(self, items: list[BundlePlanItem]) -> list[BundleCompatibilityCheck]:
        categories = {item.category for item in items}
        checks = []
        if {"电脑", "显示器"}.issubset(categories):
            checks.append(BundleCompatibilityCheck(title="显示连接", status="needs_confirmation", message="购买前确认电脑接口与显示器线材匹配。"))
        if {"显示器", "支架"}.issubset(categories):
            checks.append(BundleCompatibilityCheck(title="桌面空间", status="needs_confirmation", message="显示器和支架需要确认桌面深度。"))
        if not checks:
            checks.append(BundleCompatibilityCheck(title="搭配风险", status="pass", message="核心品类之间暂无明显搭配冲突。"))
        return checks

    def _availability_status(self, items: list[BundlePlanItem]) -> str:
        if any(item.product.conflicts for item in items):
            return "partially_available"
        return "available"

    def _role_for(self, category: str) -> str:
        roles = {
            "电脑": "性能核心",
            "显示器": "显示体验",
            "机械键盘": "输入体验",
            "鼠标": "指针控制",
            "蓝牙耳机": "会议与降噪",
            "台灯": "学习照明",
            "支架": "桌面人体工学",
            "拓展坞": "接口扩展",
            "插排": "供电补齐",
        }
        return roles.get(category, "方案补充")

    def _scenario_fit(self, need: Any) -> str:
        scenario = self._get_value(need, "scenario")
        if scenario:
            return f"{scenario}桌面、办公学习和日常电子设备使用"
        return "学习、办公、编程和日常桌面使用"

    def _sum_reasonable_baseline(self, category_cards: dict[str, list[ProductCard]]) -> float:
        total = 0.0
        for category in self.REQUIRED_DESKTOP_CATEGORIES:
            cards = category_cards.get(category, [])
            if cards:
                total += cards[0].price
        return total or 6000.0

    def _category_from_name(self, name: str) -> str | None:
        for category in self.REQUIRED_DESKTOP_CATEGORIES + self.SUPPORT_DESKTOP_CATEGORIES:
            if category in name:
                return category
        if "主机" in name or "笔记本" in name:
            return "电脑"
        return None

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
        }.get(category, {category})
        return bool(aliases & owned_categories)

    def _optional_float(self, value: Any) -> float | None:
        if value in (None, ""):
            return None
        return float(value)
