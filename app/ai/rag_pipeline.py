"""RAG pipeline orchestration."""

from __future__ import annotations

from collections import Counter
import time
from collections.abc import Callable
import re
from typing import Any

from sqlalchemy.orm import Session

from app.core.concurrency import run_blocking_io
from app.core.metrics import count_rag_empty_results, count_rag_fallback
from app.models.product import Product
from app.repositories.price_repo import PriceHistoryRepository
from app.repositories.product_repo import ProductRepository
from app.repositories.review_repo import ReviewRepository
from app.ai.rag_policy import RagFallbackPolicy, RagFilterPolicy, RagRerankPolicy
from app.utils.taxonomy import CATEGORY_KEYWORDS
from app.utils.logging import get_logger
from app.utils.text_builder import build_query_from_need
from app.vectorstore.chroma_client import ChromaProductStore
from app.vectorstore.retrieval_gateway import VectorRetrievalGateway


logger = get_logger(__name__)

class RAGPipeline:
    def __init__(
        self,
        product_store: VectorRetrievalGateway | None = None,
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
        search_results, candidates, filtered, filter_reasons, fallback_stage = self._retrieve_products(repo, need, top_k)
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

    def _retrieve_products(
        self,
        repo: ProductRepository,
        need: Any,
        top_k: int,
    ) -> tuple[list[dict], list[Product], list[Product], Counter[str], str]:
        if self._should_use_popular_fallback(need):
            return self._retrieve_popular_fallback(repo, need, top_k)
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
        return search_results, candidates, filtered, filter_reasons, fallback_stage

    def _retrieve_popular_fallback(
        self,
        repo: ProductRepository,
        need: Any,
        top_k: int,
    ) -> tuple[list[dict], list[Product], list[Product], Counter[str], str]:
        stage = "fallback_popular"
        candidates = self._fallback_candidates_for_stage(repo, need, stage, top_k)
        filtered, reasons = self.filter_policy.get_filtered_products(candidates, need, stage=stage)
        count_rag_fallback("chat", stage)
        if not filtered:
            count_rag_empty_results("chat", "database")
        return [], candidates, filtered, reasons, stage

    def _should_use_popular_fallback(self, need: Any) -> bool:
        intent = self._get_need_value(need, "intent")
        if intent not in {None, "商品推荐", "recommend"}:
            return False
        keys = ["category", "budget_max", "scenario", "preferences", "avoid", "style_preferences"]
        return not any(self._has_need_value(self._get_need_value(need, key)) for key in keys)

    def _has_need_value(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, list | tuple | set):
            return bool(value)
        return True

    def _search_vector_store(self, need: Any, top_k: int) -> list[dict]:
        query = build_query_from_need(need)
        try:
            return self.product_store.search(query, top_k=top_k)
        except Exception:
            logger.error(
                "RAG pipeline vector search failed; falling back to database candidates",
                exc_info=True,
                extra={"top_k": top_k},
            )
            return []

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
            filtered = self._guard_fallback_category(filtered, need, stage)
            if candidates and not filtered:
                reasons["fallback_category_mismatch"] += len(candidates)
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
        if stage == "fallback_keyword":
            return self._keyword_candidates(repo, need, page_size)
        if stage == "fallback_popular":
            return self._popular_candidates(repo, page_size)
        return self._adjacent_category_candidates(repo, category, page_size)

    def _guard_fallback_category(self, products: list[Product], need: Any, stage: str) -> list[Product]:
        category = self._get_need_value(need, "category")
        if not category or stage in {"fallback_budget", "fallback_relaxed"}:
            return products
        if stage == "fallback_adjacent":
            allowed = set(self.fallback_policy.list_adjacent_categories(category))
            return [product for product in products if product.category in allowed]
        if category in CATEGORY_KEYWORDS:
            return [product for product in products if product.category == category]
        if stage == "fallback_popular":
            return []
        return [
            product
            for product in products
            if self._product_matches_non_standard_target(product, str(category))
        ]

    def _product_matches_non_standard_target(self, product: Product, category: str) -> bool:
        target = category.strip().lower()
        if not target:
            return False
        searchable = " ".join(
            str(value or "")
            for value in [
                product.name,
                product.category,
                product.description,
                product.review_summary,
                product.tags,
                product.suitable_scene,
                product.specs,
            ]
        ).lower()
        return target in searchable

    def _keyword_candidates(
        self,
        repo: ProductRepository,
        need: Any,
        page_size: int,
    ) -> list[Product]:
        candidates: list[Product] = []
        seen_ids: set[int] = set()
        for keyword in self._keywords_from_need(need):
            products, _ = repo.list_products(keyword=keyword, page=1, page_size=page_size)
            for product in products:
                if product.id in seen_ids:
                    continue
                seen_ids.add(product.id)
                candidates.append(product)
                if len(candidates) >= page_size:
                    return candidates
        return candidates

    def _popular_candidates(self, repo: ProductRepository, page_size: int) -> list[Product]:
        products, _ = repo.list_products(page=1, page_size=max(page_size, 50))
        return sorted(products, key=self._fallback_sort_key)[:page_size]

    def _keywords_from_need(self, need: Any) -> list[str]:
        raw_values = [
            self._get_need_value(need, "category"),
            self._get_need_value(need, "scenario"),
            *self._coerce_list(self._get_need_value(need, "preferences")),
            *self._coerce_list(self._get_need_value(need, "avoid")),
            *self._coerce_list(self._get_need_value(need, "style_preferences")),
        ]
        keywords: list[str] = []
        for value in raw_values:
            if value in (None, ""):
                continue
            text = str(value).strip()
            if not text:
                continue
            keywords.append(text)
            keywords.extend(self._split_keyword_terms(text))
        return self._dedupe_keywords(keywords)

    def _split_keyword_terms(self, text: str) -> list[str]:
        return [
            term
            for term in re.split(r"[\s,，、。；;:/\\|]+", text)
            if len(term.strip()) >= 2
        ]

    def _dedupe_keywords(self, keywords: list[str]) -> list[str]:
        result = []
        seen = set()
        for keyword in keywords:
            normalized = keyword.strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            result.append(normalized)
        return result

    def _coerce_list(self, value: Any) -> list[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, tuple | set):
            return list(value)
        return [value]

    def _fallback_sort_key(self, product: Product) -> tuple[int, int, float, float, int]:
        has_stock = 1 if (product.stock is None or product.stock > 0) else 0
        has_price = 1 if product.price is not None else 0
        rating = float(product.rating or 0)
        sales = float(product.sales or 0)
        return (-has_stock, -has_price, -rating, -sales, product.id)

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
