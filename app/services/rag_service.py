"""RAG search service."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal
import time
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.product_repo import ProductRepository
from app.schemas.rag import RagSearchRequest, RagSearchResponse
from app.utils.logging import get_logger
from app.vectorstore.chroma_client import ChromaProductStore


logger = get_logger(__name__)


class RagService:
    def __init__(self, product_store: ChromaProductStore | None = None) -> None:
        self.product_store = product_store or ChromaProductStore()

    def search(self, request: RagSearchRequest, db: Session) -> RagSearchResponse:
        started_at = time.perf_counter()
        vector_items, diagnostics = self._valid_vector_items(request, db)
        if vector_items:
            items = vector_items[: request.top_k]
            self._log_search("vector", request, items, diagnostics, started_at)
            return RagSearchResponse(query=request.query, items=items, total=len(items))

        fallback_items = self._search_database(request, db)
        self._log_search("database", request, fallback_items, diagnostics, started_at)
        return RagSearchResponse(
            query=request.query,
            items=fallback_items,
            total=len(fallback_items),
        )

    def _log_search(
        self,
        source: str,
        request: RagSearchRequest,
        items: list[dict[str, Any]],
        diagnostics: dict[str, Any],
        started_at: float,
    ) -> None:
        logger.info(
            "RAG search completed",
            extra=self._log_extra(source, request, items, diagnostics, started_at),
        )

    def _log_extra(
        self,
        source: str,
        request: RagSearchRequest,
        items: list[dict[str, Any]],
        diagnostics: dict[str, Any],
        started_at: float,
    ) -> dict[str, Any]:
        return {
            "source": source,
            "fallback_stage": "none" if source == "vector" else "database",
            "top_k": request.top_k,
            "vector_result_count": diagnostics["vector_result_count"],
            "candidate_count": diagnostics["candidate_count"],
            "result_count": len(items),
            "filter_reasons": diagnostics["filter_reasons"],
            "retrieved_ids": diagnostics["retrieved_ids"],
            "final_ids": self._item_product_ids(items),
            "latency_ms": round((time.perf_counter() - started_at) * 1000, 2),
        }

    def _item_product_ids(self, items: list[dict[str, Any]]) -> list[int]:
        return [int(item["product_id"]) for item in items if item.get("product_id") is not None]

    def _valid_vector_items(
        self,
        request: RagSearchRequest,
        db: Session,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        vector_items = self._search_vector_store(request)
        diagnostics = self._initial_diagnostics(vector_items)
        if not vector_items:
            return [], diagnostics
        repo = ProductRepository(db)
        product_ids = [int(item["product_id"]) for item in vector_items]
        valid_ids = {product.id for product in repo.get_by_ids(product_ids)}
        diagnostics["candidate_count"] = len(vector_items)
        reasons: Counter[str] = Counter()
        valid_items = []
        for item in vector_items:
            if int(item["product_id"]) not in valid_ids:
                reasons["stale_index"] += 1
                continue
            reason = self._filter_reason(item, request)
            if reason:
                reasons[reason] += 1
                continue
            valid_items.append(item)
        diagnostics["filter_reasons"] = dict(reasons)
        return valid_items, diagnostics

    def _initial_diagnostics(self, vector_items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "vector_result_count": len(vector_items),
            "candidate_count": 0,
            "filter_reasons": {},
            "retrieved_ids": self._item_product_ids(vector_items),
        }

    def _search_vector_store(self, request: RagSearchRequest) -> list[dict[str, Any]]:
        results = self.product_store.search(request.query, top_k=request.top_k)
        items = []
        for result in results:
            metadata = result.get("metadata", {})
            product_id = metadata.get("product_id")
            if product_id is None:
                continue
            items.append(
                {
                    "product_id": product_id,
                    "name": metadata.get("name") or result.get("id"),
                    "category": metadata.get("category"),
                    "platform": metadata.get("platform"),
                    "product_url": metadata.get("product_url"),
                    "stock_status": metadata.get("stock_status"),
                    "price": metadata.get("price"),
                    "score": result.get("score"),
                    "reason": "\u5411\u91cf\u53ec\u56de\u7ed3\u679c",
                }
            )
        return items

    def _search_database(self, request: RagSearchRequest, db: Session) -> list[dict[str, Any]]:
        filters = request.filters or {}
        repo = ProductRepository(db)
        products, _ = repo.list_products(
            category=filters.get("category"),
            price_max=filters.get("price_max"),
            page=1,
            page_size=request.top_k,
        )

        return [
            {
                "product_id": product.id,
                "name": product.name,
                "price": self._to_float(product.price),
                "score": 1.0,
                "reason": "\u6570\u636e\u5e93 fallback \u7ed3\u679c",
            }
            for product in products
        ]

    def _matches_filters(self, item: dict[str, Any], request: RagSearchRequest) -> bool:
        return self._filter_reason(item, request) is None

    def _filter_reason(self, item: dict[str, Any], request: RagSearchRequest) -> str | None:
        filters = request.filters or {}
        category = filters.get("category")
        price_max = filters.get("price_max")
        if category and item.get("category") != category:
            return "category_mismatch"
        if price_max is not None and self._exceeds_price(item.get("price"), price_max):
            return "over_budget"
        return None

    def _exceeds_price(self, price: Any, price_max: Any) -> bool:
        if price is None:
            return False
        return Decimal(str(price)) > Decimal(str(price_max))

    def _to_float(self, value: object) -> float | None:
        if value is None:
            return None
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
