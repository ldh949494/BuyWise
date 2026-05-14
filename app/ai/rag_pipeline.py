"""RAG pipeline orchestration."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.product import Product
from app.repositories.product_repo import ProductRepository
from app.utils.text_builder import build_query_from_need
from app.vectorstore.chroma_client import ChromaProductStore


class RAGPipeline:
    def __init__(self, product_store: ChromaProductStore | None = None) -> None:
        self.product_store = product_store or ChromaProductStore()

    async def search_products(
        self,
        need: Any,
        db: Session,
        top_k: int = 20,
    ) -> list[Product]:
        query = build_query_from_need(need)
        repo = ProductRepository(db)

        search_results = self.product_store.search(query, top_k=top_k)
        if search_results:
            product_ids = self._extract_product_ids(search_results)
            products = repo.get_by_ids(product_ids)
            products_by_id = {product.id: product for product in products}
            candidates = [
                products_by_id[product_id]
                for product_id in product_ids
                if product_id in products_by_id
            ]
        else:
            candidates, _ = repo.list_products(
                category=self._get_need_value(need, "category"),
                price_max=self._get_need_value(need, "budget_max"),
                page=1,
                page_size=top_k,
            )

        return self._filter_products(candidates, need)[:top_k]

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
            if budget_max is not None and product.price is not None:
                if Decimal(str(product.price)) > Decimal(str(budget_max)):
                    continue
            if product.stock is not None and product.stock <= 0:
                continue
            filtered.append(product)
        return filtered

    def _get_need_value(self, need: Any, key: str) -> Any:
        if isinstance(need, dict):
            return need.get(key)
        return getattr(need, key, None)
