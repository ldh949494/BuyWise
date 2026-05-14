"""Product comparison service."""

from __future__ import annotations

import json
import re
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.ai.llm_client import LLMClient
from app.repositories.product_repo import ProductRepository
from app.schemas.compare import CompareItem, CompareResponse


class CompareService:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    async def compare(
        self,
        product_ids: list[int],
        user_need: str | None,
        db: Session,
    ) -> CompareResponse:
        products = ProductRepository(db).get_by_ids(product_ids)
        ordered_products = self._order_by_requested_ids(products, product_ids)
        items = [self._build_item(product, user_need or "") for product in ordered_products]
        items = sorted(items, key=lambda item: item.score or 0, reverse=True)

        summary = await self.llm_client.generate_compare_summary(user_need or "", items)
        winner_id = items[0].product_id if items else None
        return CompareResponse(items=items, summary=summary, winner_id=winner_id)

    def _order_by_requested_ids(self, products: list[Any], product_ids: list[int]) -> list[Any]:
        products_by_id = {product.id: product for product in products}
        return [products_by_id[product_id] for product_id in product_ids if product_id in products_by_id]

    def _build_item(self, product: Any, user_need: str) -> CompareItem:
        pros = []
        cons = []
        score = 0.0

        tags = self._coerce_list(product.tags)
        scenes = self._coerce_list(product.suitable_scene)
        specs = self._coerce_dict(product.specs)
        price = product.price
        budget = self._extract_budget(user_need)

        if self._need_quiet(user_need):
            if self._contains_any(tags, ["\u5b89\u9759", "\u9759\u97f3", "\u4f4e\u566a\u97f3"]):
                pros.append("\u5b89\u9759")
                score += 20
            else:
                cons.append("\u9759\u97f3\u4fe1\u606f\u4e0d\u660e\u786e")

        if budget is not None and price is not None:
            if Decimal(str(price)) <= Decimal(str(budget)):
                pros.append("\u4ef7\u683c\u5408\u9002")
                score += 20
            else:
                cons.append("\u8d85\u51fa\u9884\u7b97")

        if "\u5bbf\u820d" in user_need:
            if "\u5bbf\u820d" in scenes:
                pros.append("\u9002\u5408\u5bbf\u820d")
                score += 15
            else:
                cons.append("\u5bbf\u820d\u573a\u666f\u5339\u914d\u4e00\u822c")

        if "\u5199\u4ee3\u7801" in user_need or product.category == "\u673a\u68b0\u952e\u76d8":
            if (
                "\u5199\u4ee3\u7801" in scenes
                or product.category == "\u673a\u68b0\u952e\u76d8"
                or self._contains_any(tags, ["\u7f16\u7a0b", "\u529e\u516c"])
            ):
                pros.append("\u9002\u5408\u5199\u4ee3\u7801")
                score += 15
            else:
                cons.append("\u5199\u4ee3\u7801\u573a\u666f\u4e0d\u7a81\u51fa")

        if "\u65e0\u7ebf" in user_need or "\u901a\u52e4" in user_need:
            if self._supports_wireless(tags, specs):
                pros.append("\u652f\u6301\u65e0\u7ebf")
                score += 10
            else:
                cons.append("\u4e0d\u652f\u6301\u65e0\u7ebf")
        elif not self._supports_wireless(tags, specs):
            cons.append("\u4e0d\u652f\u6301\u65e0\u7ebf")

        rating = self._to_float(product.rating)
        if rating is not None:
            score += min(max(rating, 0), 5) / 5 * 15

        if product.stock is not None and product.stock > 0:
            score += 5

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

    def _coerce_list(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            parsed = self._try_parse_json(value)
            if isinstance(parsed, list):
                return [str(item) for item in parsed if item]
            return [part.strip() for part in value.split(",") if part.strip()]
        if isinstance(value, list):
            return [str(item) for item in value if item]
        return [str(value)]

    def _coerce_dict(self, value: Any) -> dict[str, Any]:
        if value is None:
            return {}
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            parsed = self._try_parse_json(value)
            if isinstance(parsed, dict):
                return parsed
        return {}

    def _try_parse_json(self, value: str) -> Any:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None

    def _to_float(self, value: Any) -> float | None:
        if value is None:
            return None
        return float(value)
