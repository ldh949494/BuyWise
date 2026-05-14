"""RAG API endpoints."""

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.product_repo import ProductRepository
from app.schemas.rag import RagSearchRequest, RagSearchResponse
from app.vectorstore.chroma_client import ChromaProductStore


router = APIRouter(prefix="/rag")


def get_product_store() -> ChromaProductStore:
    return ChromaProductStore()


@router.post("/search", response_model=RagSearchResponse)
def search_rag(
    request: RagSearchRequest,
    db: Session = Depends(get_db),
    product_store: ChromaProductStore = Depends(get_product_store),
) -> RagSearchResponse:
    vector_items = _search_vector_store(request, product_store)
    if vector_items:
        return RagSearchResponse(
            query=request.query,
            items=vector_items[: request.top_k],
            total=len(vector_items[: request.top_k]),
        )

    fallback_items = _search_database(request, db)
    return RagSearchResponse(
        query=request.query,
        items=fallback_items,
        total=len(fallback_items),
    )


def _search_vector_store(
    request: RagSearchRequest,
    product_store: ChromaProductStore,
) -> list[dict[str, Any]]:
    results = product_store.search(request.query, top_k=request.top_k)
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
                "price": metadata.get("price"),
                "score": result.get("score"),
                "reason": "\u5411\u91cf\u53ec\u56de\u7ed3\u679c",
            }
        )
    return items


def _search_database(request: RagSearchRequest, db: Session) -> list[dict[str, Any]]:
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
            "price": _to_float(product.price),
            "score": 1.0,
            "reason": "\u6570\u636e\u5e93 fallback \u7ed3\u679c",
        }
        for product in products
    ]


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)
