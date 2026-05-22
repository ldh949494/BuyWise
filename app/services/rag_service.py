"""RAG search service."""

from __future__ import annotations

from decimal import Decimal
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
        vector_items = self._valid_vector_items(request, db)
        if vector_items:
            items = vector_items[: request.top_k]
            logger.info(
                "RAG search completed",
                extra={"source": "vector", "top_k": request.top_k, "result_count": len(items)},
            )
            return RagSearchResponse(query=request.query, items=items, total=len(items))

        fallback_items = self._search_database(request, db)
        logger.info(
            "RAG search completed",
            extra={"source": "database", "top_k": request.top_k, "result_count": len(fallback_items)},
        )
        return RagSearchResponse(
            query=request.query,
            items=fallback_items,
            total=len(fallback_items),
        )

    def _valid_vector_items(self, request: RagSearchRequest, db: Session) -> list[dict[str, Any]]:
        vector_items = self._search_vector_store(request)
        if not vector_items:
            return []
        repo = ProductRepository(db)
        product_ids = [int(item["product_id"]) for item in vector_items]
        valid_ids = {product.id for product in repo.get_by_ids(product_ids)}
        return [
            item
            for item in vector_items
            if int(item["product_id"]) in valid_ids and self._matches_filters(item, request)
        ]

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
        filters = request.filters or {}
        category = filters.get("category")
        price_max = filters.get("price_max")
        if category and item.get("category") != category:
            return False
        if price_max is not None and self._exceeds_price(item.get("price"), price_max):
            return False
        return True

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
