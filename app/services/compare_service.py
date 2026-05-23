"""Product comparison service."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.ai.llm_client import LLMClient
from app.core.concurrency import run_blocking_io
from app.repositories.price_repo import PriceHistoryRepository
from app.repositories.product_repo import ProductRepository
from app.repositories.review_repo import ReviewRepository
from app.schemas.compare import CompareItem, CompareResponse
from app.services.review_signal_service import ReviewSignalService
from app.utils.compare_signals import score_price_signal, score_review_counts, score_verified_feedback
from app.utils.list_values import coerce_string_list, parse_json_or_none


class CompareService:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    async def compare(
        self,
        product_ids: list[int],
        user_need: str | None,
        db: Session,
    ) -> CompareResponse:
        items = await run_blocking_io(self._build_items, product_ids, user_need or "", db)
        summary = await self.llm_client.generate_compare_summary(user_need or "", items)
        winner_id = items[0].product_id if items else None
        return CompareResponse(items=items, summary=summary, winner_id=winner_id)

    def _build_items(
        self,
        product_ids: list[int],
        user_need: str,
        db: Session,
    ) -> list[CompareItem]:
        products = ProductRepository(db).get_by_ids(product_ids)
        ordered_products = self._order_by_requested_ids(products, product_ids)
        ids = [product.id for product in ordered_products]
        price_averages = PriceHistoryRepository(db).get_average_by_product_ids(ids)
        review_counts = ReviewRepository(db).get_sentiment_counts_by_product_ids(ids)
        feedback_metrics = ReviewSignalService(ReviewRepository(db)).get_metrics_for_products(ids)
        items = [
            self._build_item(
                product,
                user_need,
                price_averages.get(product.id),
                review_counts.get(product.id, {}),
                feedback_metrics.get(product.id, {}),
            )
            for product in ordered_products
        ]
        return sorted(items, key=lambda item: item.score or 0, reverse=True)

    def _order_by_requested_ids(self, products: list[Any], product_ids: list[int]) -> list[Any]:
        products_by_id = {product.id: product for product in products}
        return [products_by_id[product_id] for product_id in product_ids if product_id in products_by_id]

    def _build_item(
        self,
        product: Any,
        user_need: str,
        average_price: float | None = None,
        review_counts: dict[str, int] | None = None,
        feedback_metrics: dict[str, Any] | None = None,
    ) -> CompareItem:
        pros = []
        cons = []
        tags = coerce_string_list(product.tags)
        scenes = coerce_string_list(product.suitable_scene)
        specs = self._coerce_dict(product.specs)
        rating = self._to_float(product.rating)
        score = self._score_item(
            product,
            user_need,
            {"tags": tags, "scenes": scenes, "specs": specs},
            average_price,
            review_counts or {},
            feedback_metrics or {},
            pros,
            cons,
        )
        return self._item_from_product(product, specs, rating, score, pros, cons)

    def _item_from_product(
        self,
        product: Any,
        specs: dict[str, Any],
        rating: float | None,
        score: float,
        pros: list[str],
        cons: list[str],
    ) -> CompareItem:
        return CompareItem(
            id=product.id,
            product_id=product.id,
            name=product.name,
            price=self._to_float(product.price),
            image_url=product.image_url,
            rating=rating,
            score=round(score, 2),
            pros=pros,
            cons=cons,
            specs=specs,
        )

    def _score_item(
        self,
        product: Any,
        user_need: str,
        context: dict[str, Any],
        average_price: float | None,
        review_counts: dict[str, int],
        feedback_metrics: dict[str, Any],
        pros: list[str],
        cons: list[str],
    ) -> float:
        return sum(
            [
                self._score_quiet_need(user_need, context["tags"], pros, cons),
                self._score_budget(product, user_need, pros, cons),
                self._score_scene_need(product, user_need, context, pros, cons),
                self._score_wireless_need(user_need, context, pros, cons),
                self._score_reputation(product),
                self._score_stock(product),
                self._score_quality_signals(product, average_price, review_counts, feedback_metrics, pros, cons),
            ]
        )

    def _score_quiet_need(self, user_need: str, tags: list[str], pros: list[str], cons: list[str]) -> float:
        if not self._need_quiet(user_need):
            return 0.0
        if self._contains_any(tags, ["\u5b89\u9759", "\u9759\u97f3", "\u4f4e\u566a\u97f3"]):
            pros.append("\u5b89\u9759")
            return 20.0
        cons.append("\u9759\u97f3\u4fe1\u606f\u4e0d\u660e\u786e")
        return 0.0

    def _score_budget(self, product: Any, user_need: str, pros: list[str], cons: list[str]) -> float:
        budget = self._extract_budget(user_need)
        if budget is None or product.price is None:
            return 0.0
        if Decimal(str(product.price)) <= Decimal(str(budget)):
            pros.append("\u4ef7\u683c\u5408\u9002")
            return 20.0
        cons.append("\u8d85\u51fa\u9884\u7b97")
        return 0.0

    def _score_scene_need(
        self,
        product: Any,
        user_need: str,
        context: dict[str, Any],
        pros: list[str],
        cons: list[str],
    ) -> float:
        dorm_score = self._score_dorm_need(user_need, context["scenes"], pros, cons)
        coding_score = self._score_coding_need(product, user_need, context, pros, cons)
        return dorm_score + coding_score

    def _score_dorm_need(self, user_need: str, scenes: list[str], pros: list[str], cons: list[str]) -> float:
        if "\u5bbf\u820d" not in user_need:
            return 0.0
        if "\u5bbf\u820d" in scenes:
            pros.append("\u9002\u5408\u5bbf\u820d")
            return 15.0
        cons.append("\u5bbf\u820d\u573a\u666f\u5339\u914d\u4e00\u822c")
        return 0.0

    def _score_coding_need(
        self,
        product: Any,
        user_need: str,
        context: dict[str, Any],
        pros: list[str],
        cons: list[str],
    ) -> float:
        if "\u5199\u4ee3\u7801" not in user_need and product.category != "\u673a\u68b0\u952e\u76d8":
            return 0.0
        if self._matches_coding_need(product, context):
            pros.append("\u9002\u5408\u5199\u4ee3\u7801")
            return 15.0
        cons.append("\u5199\u4ee3\u7801\u573a\u666f\u4e0d\u7a81\u51fa")
        return 0.0

    def _matches_coding_need(self, product: Any, context: dict[str, Any]) -> bool:
        return (
            "\u5199\u4ee3\u7801" in context["scenes"]
            or product.category == "\u673a\u68b0\u952e\u76d8"
            or self._contains_any(context["tags"], ["\u7f16\u7a0b", "\u529e\u516c"])
        )

    def _score_wireless_need(self, user_need: str, context: dict[str, Any], pros: list[str], cons: list[str]) -> float:
        supports_wireless = self._supports_wireless(context["tags"], context["specs"])
        if "\u65e0\u7ebf" in user_need or "\u901a\u52e4" in user_need:
            if supports_wireless:
                pros.append("\u652f\u6301\u65e0\u7ebf")
                return 10.0
            cons.append("\u4e0d\u652f\u6301\u65e0\u7ebf")
            return 0.0
        if not supports_wireless:
            cons.append("\u4e0d\u652f\u6301\u65e0\u7ebf")
        return 0.0

    def _score_reputation(self, product: Any) -> float:
        rating = self._to_float(product.rating)
        if rating is None:
            return 0.0
        return min(max(rating, 0), 5) / 5 * 15

    def _score_stock(self, product: Any) -> float:
        return 5.0 if product.stock is not None and product.stock > 0 else 0.0

    def _score_quality_signals(
        self,
        product: Any,
        average_price: float | None,
        review_counts: dict[str, int],
        feedback_metrics: dict[str, Any],
        pros: list[str],
        cons: list[str],
    ) -> float:
        return sum(
            [
                score_price_signal(product, average_price, pros, cons),
                score_review_counts(review_counts, pros, cons),
                score_verified_feedback(feedback_metrics, pros, cons),
            ]
        )

    def _extract_budget(self, text: str) -> float | None:
        match = re.search(r"(\d+(?:\.\d+)?)\s*(?:\u5143|\u5757)?\s*(?:\u4ee5\u5185|\u4ee5\u4e0b|\u4e4b\u5185)", text)
        if not match:
            match = re.search(r"\u9884\u7b97\s*(\d+(?:\.\d+)?)", text)
        if not match:
            return None
        value = float(match.group(1))
        return int(value) if value.is_integer() else value

    def _need_quiet(self, text: str) -> bool:
        return any(keyword in text for keyword in ["\u5b89\u9759", "\u9759\u97f3", "\u58f0\u97f3\u5c0f", "\u4f4e\u566a\u97f3"])

    def _supports_wireless(self, tags: list[str], specs: dict[str, Any]) -> bool:
        values = tags + [str(value) for value in specs.values()]
        return self._contains_any(values, ["\u65e0\u7ebf", "\u84dd\u7259", "2.4G"])

    def _contains_any(self, values: list[str], keywords: list[str]) -> bool:
        return any(keyword in value for value in values for keyword in keywords)

    def _coerce_dict(self, value: Any) -> dict[str, Any]:
        if value is None:
            return {}
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            parsed = parse_json_or_none(value)
            if isinstance(parsed, dict):
                return parsed
        return {}

    def _to_float(self, value: Any) -> float | None:
        if value is None:
            return None
        return float(value)
