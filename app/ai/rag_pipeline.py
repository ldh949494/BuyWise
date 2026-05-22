"""RAG pipeline orchestration."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.core.concurrency import run_blocking_io
from app.models.product import Product
from app.repositories.product_repo import ProductRepository
from app.utils.logging import get_logger
from app.utils.text_builder import build_query_from_need
from app.vectorstore.chroma_client import ChromaProductStore


logger = get_logger(__name__)


class RAGPipeline:
    def __init__(self, product_store: ChromaProductStore | None = None) -> None:
        self.product_store = product_store or ChromaProductStore()

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
        repo = ProductRepository(db)
        search_results = self._search_vector_store(need, top_k)
        candidates = self._build_candidates(repo, need, search_results, top_k)
        filtered = self._filter_products(candidates, need)[:top_k]
        self._log_search(search_results, top_k, candidates, filtered)
        return filtered

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
        search_results: list[dict],
        top_k: int,
        candidates: list[Product],
        filtered: list[Product],
    ) -> None:
        logger.info(
            "RAG pipeline search completed",
            extra={
                "source": "vector" if search_results else "database",
                "top_k": top_k,
                "candidate_count": len(candidates),
                "result_count": len(filtered),
            },
        )

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

    def _filter_products(self, products: list[Product], need: Any) -> list[Product]:
        category = self._get_need_value(need, "category")
        budget_max = self._get_need_value(need, "budget_max")

        filtered = []
        for product in products:
            if category and product.category != category:
                continue
            if self._exceeds_budget(product, budget_max):
                continue
            if product.stock is not None and product.stock <= 0:
                continue
            filtered.append(product)
        return filtered

    def _exceeds_budget(self, product: Product, budget_max: Any) -> bool:
        if budget_max is None or product.price is None:
            return False
        return Decimal(str(product.price)) > Decimal(str(budget_max))

    def _get_need_value(self, need: Any, key: str) -> Any:
        if isinstance(need, dict):
            return need.get(key)
        return getattr(need, key, None)
