"""RAG search service."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal
import time
from typing import Any

from sqlalchemy.orm import Session

from app.core.metrics import count_rag_empty_results, count_rag_fallback
from app.models.product import Product
from app.repositories.product_repo import ProductRepository
from app.schemas.rag import RagItem, RagSearchRequest, RagSearchResponse
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
        count_rag_fallback("rag_search", "database")
        if not fallback_items:
            count_rag_empty_results("rag_search", "database")
        return RagSearchResponse(
            query=request.query,
            items=fallback_items,
            total=len(fallback_items),
        )

    def _log_search(
        self,
        source: str,
        request: RagSearchRequest,
        items: list[RagItem],
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
        items: list[RagItem],
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

    def _item_product_ids(self, items: list[RagItem]) -> list[int]:
        return [item.product_id for item in items]

    def _valid_vector_items(
        self,
        request: RagSearchRequest,
        db: Session,
    ) -> tuple[list[RagItem], dict[str, Any]]:
        vector_items = self._search_vector_store(request)
        diagnostics = self._initial_diagnostics(vector_items)
        if not vector_items:
            return [], diagnostics
        repo = ProductRepository(db)
        product_ids = [item.product_id for item in vector_items]
        products_by_id = {product.id: product for product in repo.get_by_ids(product_ids)}
        diagnostics["candidate_count"] = len(vector_items)
        reasons: Counter[str] = Counter()
        valid_items = []
        for item in vector_items:
            product = products_by_id.get(item.product_id)
            if product is None:
                reasons["stale_index"] += 1
                continue
            refreshed_item = self._item_from_product(
                product,
                score=item.score,
                reason="\u5411\u91cf\u53ec\u56de\u7ed3\u679c",
            )
            reason = self._filter_reason(refreshed_item, request)
            if reason:
                reasons[reason] += 1
                continue
            valid_items.append(refreshed_item)
        diagnostics["filter_reasons"] = dict(reasons)
        return valid_items, diagnostics

    def _initial_diagnostics(self, vector_items: list[RagItem]) -> dict[str, Any]:
        return {
            "vector_result_count": len(vector_items),
            "candidate_count": 0,
            "filter_reasons": {},
            "retrieved_ids": self._item_product_ids(vector_items),
        }

    def _search_vector_store(self, request: RagSearchRequest) -> list[RagItem]:
        try:
            results = self.product_store.search(request.query, top_k=request.top_k)
        except Exception:
            logger.error(
                "RAG vector search failed; falling back to database search",
                exc_info=True,
                extra={"top_k": request.top_k},
            )
            return []
        items_by_product_id: dict[int, RagItem] = {}
        for result in results:
            metadata = result.get("metadata", {})
            product_id = metadata.get("product_id")
            if product_id is None:
                continue
            product_id = int(product_id)
            score = self._to_float(result.get("score"))
            existing = items_by_product_id.get(product_id)
            if existing is not None and (existing.score or 0.0) >= (score or 0.0):
                continue
            items_by_product_id[product_id] = RagItem(
                product_id=product_id,
                name=metadata.get("name") or result.get("id"),
                category=metadata.get("category"),
                platform=metadata.get("platform"),
                product_url=metadata.get("product_url"),
                stock_status=metadata.get("stock_status"),
                price=self._to_float(metadata.get("price")),
                score=score,
                reason="\u5411\u91cf\u53ec\u56de\u7ed3\u679c",
            )
        return list(items_by_product_id.values())

    def _search_database(self, request: RagSearchRequest, db: Session) -> list[RagItem]:
        filters = request.filters or {}
        repo = ProductRepository(db)
        products, _ = repo.list_products(
            category=filters.get("category"),
            price_max=filters.get("price_max"),
            page=1,
            page_size=request.top_k,
        )

        return [
            self._item_from_product(product, score=1.0, reason="\u6570\u636e\u5e93 fallback \u7ed3\u679c")
            for product in products
        ]

    def _matches_filters(self, item: RagItem, request: RagSearchRequest) -> bool:
        return self._filter_reason(item, request) is None

    def _filter_reason(self, item: RagItem, request: RagSearchRequest) -> str | None:
        filters = request.filters or {}
        category = filters.get("category")
        price_max = filters.get("price_max")
        if category and item.category != category:
            return "category_mismatch"
        if price_max is not None and self._exceeds_price(item.price, price_max):
            return "over_budget"
        if item.stock_status in {"out_of_stock", "discontinued"}:
            return "unavailable"
        return None

    def _item_from_product(self, product: Product, *, score: float | None, reason: str) -> RagItem:
        return RagItem(
            product_id=product.id,
            name=product.name,
            price=self._to_float(product.price),
            score=score,
            reason=reason,
            category=product.category,
            platform=product.platform,
            product_url=product.product_url,
            stock_status=product.stock_status,
        )

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
