"""Guide conversation memory helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GuideProductRef:
    product: dict[str, Any]
    snapshot: dict[str, Any]
    position: int


class GuideMemoryService:
    def __init__(self, chat_repo: Any) -> None:
        self.chat_repo = chat_repo

    def list_snapshots(self, session_id: str, limit: int = 40) -> list[dict[str, Any]]:
        records = []
        for message in self.chat_repo.list_messages(session_id, limit=limit):
            structured_data = getattr(message, "structured_data", None) or {}
            snapshot = self._snapshot(structured_data)
            if snapshot is not None:
                records.append(snapshot)
        return records

    def get_latest_snapshot(self, session_id: str) -> dict[str, Any] | None:
        snapshots = self.list_snapshots(session_id)
        return snapshots[-1] if snapshots else None

    def build_history_context(self, session_id: str) -> dict[str, Any]:
        snapshots = self.list_snapshots(session_id)
        if not snapshots:
            return {}
        active = snapshots[-1].get("need") or {}
        context = {key: value for key, value in active.items() if value not in (None, [], "")}
        categories = self._recent_categories(snapshots)
        products = self._recent_top_products(snapshots)
        if categories:
            context["recent_categories"] = categories
        if products:
            context["recent_products"] = products
        return context

    def get_product_reference(self, session_id: str, text: str) -> GuideProductRef | None:
        snapshots = self.list_snapshots(session_id)
        if not snapshots:
            return None
        category = self._reference_category_marker(text)
        ordinal = self._ordinal(text)
        candidates = list(reversed(snapshots))
        if category is not None:
            candidates = [snapshot for snapshot in candidates if self._snapshot_category(snapshot) == category]
        for snapshot in candidates:
            products = self._products(snapshot)
            if 1 <= ordinal <= len(products):
                return GuideProductRef(products[ordinal - 1], snapshot, ordinal)
        return None

    def get_latest_product_in_category(self, session_id: str, category: str) -> GuideProductRef | None:
        for snapshot in reversed(self.list_snapshots(session_id)):
            if self._snapshot_category(snapshot) != category:
                continue
            products = self._products(snapshot)
            if products:
                return GuideProductRef(products[0], snapshot, 1)
        return None

    def _snapshot(self, structured_data: dict[str, Any]) -> dict[str, Any] | None:
        if not isinstance(structured_data, dict):
            return None
        need = structured_data.get("need")
        products = structured_data.get("products") or []
        bundle_plans = structured_data.get("bundle_plans") or []
        if not isinstance(need, dict) or not (products or bundle_plans):
            return None
        return {
            "need": need,
            "products": [product for product in products if isinstance(product, dict)],
            "bundle_plans": [plan for plan in bundle_plans if isinstance(plan, dict)],
            "applied_preferences": structured_data.get("applied_preferences") or {},
        }

    def _recent_categories(self, snapshots: list[dict[str, Any]]) -> list[str]:
        categories = []
        for snapshot in reversed(snapshots):
            category = self._snapshot_category(snapshot)
            if category and category not in categories:
                categories.append(category)
        return categories[:5]

    def _recent_top_products(self, snapshots: list[dict[str, Any]]) -> list[dict[str, Any]]:
        products = []
        seen_ids = set()
        for snapshot in reversed(snapshots):
            for product in self._products(snapshot)[:1]:
                product_id = product.get("id")
                if product_id in seen_ids:
                    continue
                seen_ids.add(product_id)
                products.append(
                    {
                        "id": product_id,
                        "name": product.get("name"),
                        "category": product.get("category"),
                    }
                )
        return products[:5]

    def _snapshot_category(self, snapshot: dict[str, Any]) -> str | None:
        need = snapshot.get("need") or {}
        category = str(need.get("category") or "").strip()
        return category or None

    def _products(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        products = snapshot.get("products") or []
        if products:
            return products
        flattened = []
        for plan in snapshot.get("bundle_plans") or []:
            for item in plan.get("items") or []:
                product = item.get("product") if isinstance(item, dict) else None
                if isinstance(product, dict):
                    flattened.append(product)
        return flattened

    def _category_marker(self, text: str) -> str | None:
        markers = {
            "机械键盘": ["机械键盘", "键盘"],
            "鼠标": ["鼠标"],
            "蓝牙耳机": ["蓝牙耳机", "耳机"],
            "双肩包": ["双肩包", "背包", "书包"],
            "显示器": ["显示器", "屏幕"],
            "台灯": ["台灯"],
        }
        for category, aliases in markers.items():
            if any(alias in text for alias in aliases):
                return category
        return None

    def _reference_category_marker(self, text: str) -> str | None:
        for category, aliases in {
            "机械键盘": ["第一款键盘", "首推键盘", "这款键盘", "那个键盘"],
            "鼠标": ["第一款鼠标", "首推鼠标", "这款鼠标", "那个鼠标"],
            "蓝牙耳机": ["第一款耳机", "首推耳机", "这款耳机", "那个耳机"],
            "双肩包": ["第一款背包", "首推背包", "这款背包", "那个背包"],
            "显示器": ["第一款显示器", "首推显示器", "这款显示器", "那个显示器"],
            "台灯": ["第一款台灯", "首推台灯", "这款台灯", "那个台灯"],
        }.items():
            if any(alias in text for alias in aliases):
                return category
        return None

    def _ordinal(self, text: str) -> int:
        for marker, value in {
            "首推": 1,
            "优先推荐": 1,
            "第一": 1,
            "第1": 1,
            "第二": 2,
            "第2": 2,
            "第三": 3,
            "第3": 3,
        }.items():
            if marker in text:
                return value
        return 1
