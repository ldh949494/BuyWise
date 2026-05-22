"""Product vector index orchestration."""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.repositories.product_repo import ProductRepository
from app.utils.text_builder import build_product_text
from app.vectorstore.chroma_client import ChromaProductStore


def build_vector_index(
    session_factory: Callable[[], Session] = SessionLocal,
    store: ChromaProductStore | None = None,
    mode: str = "rebuild",
    product_ids: list[int] | None = None,
    batch_size: int = 100,
) -> dict[str, int | str | bool]:
    product_store = store or ChromaProductStore()
    deleted_collection = False
    if mode == "rebuild":
        product_store.reset()
        deleted_collection = True
    elif mode != "upsert":
        raise ValueError("mode must be 'rebuild' or 'upsert'.")

    with session_factory() as db:
        repo = ProductRepository(db)
        products = (
            repo.get_by_ids(product_ids, include_inactive=True)
            if product_ids
            else repo.get_all(include_inactive=True)
        )
        docs = [_build_product_doc(product) for product in products]

    for batch in _iter_batches(docs, batch_size):
        product_store.add_documents(batch)

    return {"indexed": len(docs), "mode": mode, "deleted_collection": deleted_collection}


def update_product_index(
    product_ids: list[int],
    session_factory: Callable[[], Session] = SessionLocal,
    store: ChromaProductStore | None = None,
) -> dict[str, int | str | bool]:
    return build_vector_index(
        session_factory=session_factory,
        store=store,
        mode="upsert",
        product_ids=product_ids,
    )


def validate_vector_index_health(
    session_factory: Callable[[], Session] = SessionLocal,
    store: ChromaProductStore | None = None,
    expected_product_ids: list[int] | None = None,
    profile: str | None = None,
) -> dict[str, object]:
    product_store = store or ChromaProductStore()
    indexed_ids = set(product_store.indexed_product_ids())
    with session_factory() as db:
        db_ids = {product.id for product in ProductRepository(db).get_all(include_inactive=True)}

    expected_ids = set(expected_product_ids or db_ids)
    missing_in_index = sorted(expected_ids - indexed_ids)
    stale_in_index = sorted(indexed_ids - db_ids)
    return {
        "ok": not missing_in_index and not stale_in_index,
        "profile": profile,
        "collection_count": product_store.count(),
        "db_product_count": len(db_ids),
        "expected_product_count": len(expected_ids),
        "indexed_product_ids": sorted(indexed_ids),
        "missing_in_index": missing_in_index,
        "stale_in_index": stale_in_index,
    }


def _build_product_doc(product) -> dict:
    return {
        "id": f"product_{product.id}",
        "text": build_product_text(product),
        "metadata": {
            "product_id": product.id,
            "name": product.name,
            "category": product.category,
            "brand": product.brand,
            "sku": product.sku,
            "platform": product.platform,
            "product_url": product.product_url,
            "price": _to_float(product.price),
            "stock_status": product.stock_status,
        },
    }


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _iter_batches(docs: list[dict], batch_size: int) -> list[list[dict]]:
    size = max(1, batch_size)
    return [docs[index : index + size] for index in range(0, len(docs), size)]
