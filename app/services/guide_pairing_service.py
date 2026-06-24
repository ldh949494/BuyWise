"""Build anchored pairing plans from guide memory."""

from __future__ import annotations

from typing import Any

from app.schemas.chat import BundleCompleteness, BundlePlan, BundlePlanItem, ProductCard


class GuidePairingService:
    def build_pairing_plans_from_context(
        self,
        context: dict[str, Any],
        products: list[Any],
        bundle_plans: list[BundlePlan],
    ) -> list[BundlePlan]:
        if bundle_plans:
            return bundle_plans
        anchor = context.get("pairing_anchor_product")
        if not isinstance(anchor, dict):
            return bundle_plans
        return self.build_pairing_plans(
            text=str(context.get("active_user_text") or ""),
            anchor=anchor,
            products=products,
        )

    def build_pairing_plans(
        self,
        *,
        text: str,
        anchor: dict[str, Any] | None,
        products: list[Any],
    ) -> list[BundlePlan]:
        if anchor is None or not self._is_pairing_request(text) or not products:
            return []
        anchor_card = ProductCard.model_validate(anchor)
        target_cards = [ProductCard.model_validate(self._dump(product)) for product in products[:3]]
        return [self._plan(anchor_card, target, index) for index, target in enumerate(target_cards, start=1)]

    def _plan(self, anchor_card: ProductCard, target: ProductCard, index: int) -> BundlePlan:
        total = round(anchor_card.price + target.price, 2)
        return BundlePlan(
            **self._plan_core(anchor_card, target, index, total),
            items=self._items(anchor_card, target),
            tradeoffs=["购买前确认接口、尺寸、无线连接方式和使用场景是否一致。"],
            compare_highlights=[f"{target.name} 用于补齐 {anchor_card.name} 的搭配需求。"],
            compatibility_checks=[{"title": "搭配关系", "status": "needs_confirmation", "message": "已按历史导购商品搭配，仍需确认个人手感、尺寸和连接偏好。"}],
        )

    def _plan_core(self, anchor_card: ProductCard, target: ProductCard, index: int, total: float) -> dict[str, Any]:
        return {
            "id": f"pairing-{anchor_card.id}-{target.id}-{index}",
            "title": f"方案{index} · {anchor_card.name} 搭配 {target.name}",
            "budget_tier": ["entry", "balanced", "premium"][min(index - 1, 2)],
            "target_budget": total,
            "total_price": total,
            "budget_status": "within_budget",
            "budget_delta": 0,
            "recommendation_level": "high" if index == 1 else "medium",
            "scenario_fit": "基于上一轮导购商品的适配搭配",
            "summary": "保留已选商品，只替换或补充本轮推荐品类。",
            "completeness": BundleCompleteness(included_required=2, expected_required=2),
        }

    def _items(self, anchor_card: ProductCard, target: ProductCard) -> list[BundlePlanItem]:
        return [
            BundlePlanItem(category=anchor_card.category or "已选商品", product=anchor_card, role="已选基础商品", required=True, replaceable=False, locked=True),
            BundlePlanItem(category=target.category or "推荐补充", product=target, role="适配补充商品", required=True),
        ]

    def _is_pairing_request(self, text: str) -> bool:
        return any(marker in text for marker in ["搭配", "适配", "配套", "匹配", "配一个", "配一款"])

    def _dump(self, value: Any) -> Any:
        if hasattr(value, "model_dump"):
            return value.model_dump(mode="json")
        return value
