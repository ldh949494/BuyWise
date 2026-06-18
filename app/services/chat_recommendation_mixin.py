"""Recommendation helpers for chat orchestration."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.repositories.price_repo import PriceHistoryRepository
from app.repositories.review_repo import ReviewRepository
from app.schemas.chat import BundlePlan
from app.services.recommendation_fallbacks import build_rag_fallback_meta, rank_with_fallback
from app.utils.logging import get_logger


logger = get_logger(__name__)


class ChatRecommendationMixin:
    async def _rank_recommendations(self, need: Any, db: Session) -> list[Any]:
        if self._is_bundle_intent(need):
            return await self._rank_bundle_recommendations(need, db)
        strategy = self._get_need_value(need, "retrieval_strategy") or "balanced"
        products = await self.rag_pipeline.search_products(need, db, top_k=self._retrieval_top_k(strategy))
        self._attach_quality_signals(products, db)
        return rank_with_fallback(
            products,
            need,
            self.recommend_service,
            get_value=self._get_need_value,
            logger=logger,
        )[: self._result_limit(strategy)]

    async def _recommendation_results(self, need: Any, db: Session) -> tuple[list[Any], list[BundlePlan]]:
        if not self._is_bundle_intent(need):
            return await self._rank_recommendations(need, db), []
        products = await self.rag_pipeline.search_products(need, db, top_k=30)
        self._attach_quality_signals(products, db)
        bundle_plans = self.bundle_recommend_service.build_plans(products, need)
        return self._flatten_bundle_plan_products(bundle_plans), bundle_plans

    async def _rank_bundle_recommendations(self, need: Any, db: Session) -> list[Any]:
        products = await self.rag_pipeline.search_products(need, db, top_k=30)
        self._attach_quality_signals(products, db)
        return self.bundle_recommend_service.rank_cards(products, need)

    def _is_bundle_intent(self, need: Any) -> bool:
        return self._get_need_value(need, "intent") in {"bundle_recommend", "场景化组合推荐"}

    def _flatten_bundle_plan_products(self, bundle_plans: list[BundlePlan]) -> list[Any]:
        products = []
        seen_ids = set()
        for plan in bundle_plans:
            for item in plan.items:
                if item.product.id in seen_ids:
                    continue
                seen_ids.add(item.product.id)
                products.append(item.product)
        return products

    def _fallback_bundle_reply(self, bundle_plans: list[BundlePlan]) -> str:
        names = "、".join(plan.title for plan in bundle_plans[:3])
        return f"我按预算档整理了 {len(bundle_plans)} 套组合方案：{names}。你可以先看总价、完整度和关键取舍，再进入方案对比。"

    def _get_need_value(self, need: Any, key: str) -> Any:
        if isinstance(need, dict):
            return need.get(key)
        return getattr(need, key, None)

    def _rag_fallback_meta(self) -> dict[str, Any]:
        return build_rag_fallback_meta(self.rag_pipeline)

    def _retrieval_top_k(self, strategy: str) -> int:
        if strategy == "explore":
            return 30
        if strategy == "strict":
            return 12
        return 20

    def _result_limit(self, strategy: str) -> int:
        return 8 if strategy == "explore" else 5

    def _attach_quality_signals(self, products: list[Any], db: Session) -> None:
        if not hasattr(db, "execute"):
            return
        product_ids = [product.id for product in products]
        price_averages = PriceHistoryRepository(db).get_average_by_product_ids(product_ids)
        review_counts = ReviewRepository(db).get_sentiment_counts_by_product_ids(product_ids)
        for product in products:
            product.price_history_average = price_averages.get(product.id)
            product.review_sentiment_counts = review_counts.get(product.id, {})
