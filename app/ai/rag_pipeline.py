"""RAG pipeline orchestration."""

from __future__ import annotations

from collections import Counter
import time
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from app.core.concurrency import run_blocking_io
from app.core.metrics import count_rag_empty_results, count_rag_fallback
from app.models.product import Product
from app.repositories.price_repo import PriceHistoryRepository
from app.repositories.product_repo import ProductRepository
from app.repositories.review_repo import ReviewRepository
from app.ai.rag_policy import RagFallbackPolicy, RagFilterPolicy, RagRerankPolicy
from app.utils.logging import get_logger
from app.utils.text_builder import build_query_from_need
from app.vectorstore.chroma_client import ChromaProductStore


logger = get_logger(__name__)

class RAGPipeline:
    def __init__(
        self,
        product_store: ChromaProductStore | None = None,
        reranker: Any | None = None,
        feedback_metrics_builder: Callable[[Session, list[int]], dict[int, dict[str, object]]] | None = None,
        fallback_policy: RagFallbackPolicy | None = None,
        filter_policy: RagFilterPolicy | None = None,
        rerank_policy: RagRerankPolicy | None = None,
    ) -> None:
        self.product_store = product_store or ChromaProductStore()
        self.reranker = reranker
        self.feedback_metrics_builder = feedback_metrics_builder
        self.fallback_policy = fallback_policy or RagFallbackPolicy()
        self.filter_policy = filter_policy or RagFilterPolicy(self.fallback_policy)
        self.rerank_policy = rerank_policy or RagRerankPolicy(reranker)
        self.last_diagnostics: dict[str, Any] = {}

    async def search_products(
        self,
        need: Any,
        db: Session,
        top_k: int = 20,
    ) -> list[Product]:
        return await run_blocking_io(self.search_products_sync, need, db, top_k)

    def search_products_sync(
        self,
        need: Any,
        db: Session,
        top_k: int = 20,
    ) -> list[Product]:
        started_at = time.perf_counter()
        repo = ProductRepository(db)
        search_results = self._search_vector_store(need, self._candidate_top_k(top_k))
        candidates = self._build_candidates(repo, need, search_results, top_k)
        filtered, filter_reasons = self.filter_policy.get_filtered_products(candidates, need)
        fallback_stage = "strict"
        if not filtered:
            filtered, fallback_stage, fallback_reasons = self._fallback_products(repo, need, top_k)
            filter_reasons.update(fallback_reasons)
            if fallback_stage != "none":
                count_rag_fallback("chat", fallback_stage)
            if not filtered:
                count_rag_empty_results("chat", "vector")
        reranked = self._rerank_products(filtered, need, db)[:top_k]
        self.last_diagnostics = self._build_diagnostics(
            search_results,
            candidates,
            reranked,
            filter_reasons,
            fallback_stage,
            started_at,
        )
        self._log_search(top_k)
        return reranked

    def _search_vector_store(self, need: Any, top_k: int) -> list[dict]:
        query = build_query_from_need(need)
        return self.product_store.search(query, top_k=top_k)

    def _build_candidates(
        self,
        repo: ProductRepository,
        need: Any,
        search_results: list[dict],
        top_k: int,
    ) -> list[Product]:
        if search_results:
            candidates = self._candidates_from_vector_results(repo, search_results)
            if candidates:
                return candidates
        return self._fallback_candidates(repo, need, top_k)

    def _candidates_from_vector_results(
        self,
        repo: ProductRepository,
        search_results: list[dict],
    ) -> list[Product]:
        product_ids = self._extract_product_ids(search_results)
        products = repo.get_by_ids(product_ids)
        products_by_id = {product.id: product for product in products}
        return [
            products_by_id[product_id]
            for product_id in product_ids
            if product_id in products_by_id
        ]

    def _fallback_candidates(
        self,
        repo: ProductRepository,
        need: Any,
        top_k: int,
    ) -> list[Product]:
        candidates, _ = repo.list_products(
            category=self._get_need_value(need, "category"),
            price_max=self._get_need_value(need, "budget_max"),
            page=1,
            page_size=top_k,
        )
        return candidates

    def _log_search(
        self,
        top_k: int,
    ) -> None:
        logger.info(
            "RAG pipeline search completed",
            extra={
                "top_k": top_k,
                **self.last_diagnostics,
            },
        )

    def _build_diagnostics(
        self,
        search_results: list[dict],
        candidates: list[Product],
        final_products: list[Product],
        filter_reasons: Counter[str],
        fallback_stage: str,
        started_at: float,
    ) -> dict[str, Any]:
        return {
            "source": "vector" if search_results else "database",
            "fallback_stage": fallback_stage,
            "filter_reasons": dict(filter_reasons),
            "retrieved_ids": self._extract_product_ids(search_results),
            "candidate_ids": [product.id for product in candidates],
            "final_ids": [product.id for product in final_products],
            "vector_result_count": len(search_results),
            "candidate_count": len(candidates),
            "result_count": len(final_products),
            "latency_ms": round((time.perf_counter() - started_at) * 1000, 2),
        }

    def _extract_product_ids(self, search_results: list[dict]) -> list[int]:
        product_ids = []
        seen = set()
        for result in search_results:
            metadata = result.get("metadata") or {}
            product_id = metadata.get("product_id")
            if product_id is None:
                continue
            product_id = int(product_id)
            if product_id not in seen:
                product_ids.append(product_id)
                seen.add(product_id)
        return product_ids

    def _fallback_products(
        self,
        repo: ProductRepository,
        need: Any,
        top_k: int,
    ) -> tuple[list[Product], str, Counter[str]]:
        for stage in self.fallback_policy.list_stages():
            candidates = self._fallback_candidates_for_stage(repo, need, stage, top_k)
            filtered, reasons = self.filter_policy.get_filtered_products(candidates, need, stage=stage)
            if filtered:
                return filtered, stage, reasons
        return [], "none", Counter()

    def _fallback_candidates_for_stage(
        self,
        repo: ProductRepository,
        need: Any,
        stage: str,
        top_k: int,
    ) -> list[Product]:
        category = self._get_need_value(need, "category")
        budget_max = self._get_need_value(need, "budget_max")
        page_size = self.fallback_policy.get_page_size(top_k)
        if stage == "fallback_budget":
            candidates, _ = repo.list_products(
                category=category,
                price_max=self.fallback_policy.get_relaxed_budget(budget_max),
                page=1,
                page_size=page_size,
            )
            return candidates
        if stage == "fallback_relaxed":
            candidates, _ = repo.list_products(category=category, page=1, page_size=page_size)
            return candidates
        return self._adjacent_category_candidates(repo, category, page_size)

    def _adjacent_category_candidates(
        self,
        repo: ProductRepository,
        category: str | None,
        page_size: int,
    ) -> list[Product]:
        candidates = []
        for adjacent in self.fallback_policy.list_adjacent_categories(category):
            products, _ = repo.list_products(category=adjacent, page=1, page_size=page_size)
            candidates.extend(products)
        return candidates

    def _rerank_products(self, products: list[Product], need: Any, db: Session) -> list[Product]:
        if not products:
            return []
        self._attach_quality_signals(products, db)
        return self.rerank_policy.rank_products(products, need)

    def _attach_quality_signals(self, products: list[Product], db: Session) -> None:
        product_ids = [product.id for product in products]
        review_repo = ReviewRepository(db)
        sentiment_counts = review_repo.get_sentiment_counts_by_product_ids(product_ids)
        feedback_metrics = self._feedback_metrics(db, product_ids)
        price_averages = PriceHistoryRepository(db).get_average_by_product_ids(product_ids)
        for product in products:
            product.review_sentiment_counts = sentiment_counts.get(product.id, {})
            product.feedback_metrics = feedback_metrics.get(product.id, {})
            product.price_history_average = price_averages.get(product.id)

    def _feedback_metrics(self, db: Session, product_ids: list[int]) -> dict[int, dict[str, object]]:
        if self.feedback_metrics_builder is None:
            return {}
        return self.feedback_metrics_builder(db, product_ids)

    def _candidate_top_k(self, top_k: int) -> int:
        return max(top_k * 3, 30)

    def _get_need_value(self, need: Any, key: str) -> Any:
        if isinstance(need, dict):
            return need.get(key)
        return getattr(need, key, None)
