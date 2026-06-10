"""Product vector index orchestration."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.repositories.product_repo import ProductRepository
from app.utils.text_builder import build_product_chunks
from app.vectorstore.chroma_client import ChromaProductStore
from app.vectorstore.retrieval_gateway import VectorRetrievalGateway


def build_vector_index(
    session_factory: Callable[[], Session] = SessionLocal,
    store: VectorRetrievalGateway | None = None,
    mode: str = "rebuild",
    product_ids: list[int] | None = None,
    batch_size: int = 100,
) -> dict[str, int | str | bool]:
    product_store = store or ChromaProductStore()
    deleted_collection = _prepare_index_store(product_store, mode)
    docs = _load_product_docs(session_factory, product_ids)
    _delete_replaced_product_documents(product_store, mode, product_ids)
    _write_product_documents(product_store, docs, batch_size)

    return {"indexed": len(docs), "mode": mode, "deleted_collection": deleted_collection}


def update_product_index(
    product_ids: list[int],
    session_factory: Callable[[], Session] = SessionLocal,
    store: VectorRetrievalGateway | None = None,
) -> dict[str, int | str | bool]:
    return build_vector_index(
        session_factory=session_factory,
        store=store,
        mode="upsert",
        product_ids=product_ids,
    )


def _prepare_index_store(product_store: VectorRetrievalGateway, mode: str) -> bool:
    if mode == "rebuild":
        product_store.reset()
        return True
    if mode != "upsert":
        raise ValueError("mode must be 'rebuild' or 'upsert'.")
    return False


def _load_product_docs(
    session_factory: Callable[[], Session],
    product_ids: list[int] | None,
) -> list[dict]:
    with session_factory() as db:
        repo = ProductRepository(db)
        products = (
            repo.get_by_ids(product_ids)
            if product_ids
            else repo.get_all()
        )
        return [doc for product in products for doc in _build_product_docs(product)]


def _delete_replaced_product_documents(
    product_store: VectorRetrievalGateway,
    mode: str,
    product_ids: list[int] | None,
) -> None:
    if mode != "upsert" or not product_ids:
        return
    for product_id in product_ids:
        product_store.delete_product_documents(product_id)


def _write_product_documents(
    product_store: VectorRetrievalGateway,
    docs: list[dict],
    batch_size: int,
) -> None:
    for batch in _iter_batches(docs, batch_size):
        product_store.add_documents(batch)


def validate_vector_index_health(
    session_factory: Callable[[], Session] = SessionLocal,
    store: VectorRetrievalGateway | None = None,
    expected_product_ids: list[int] | None = None,
    profile: str | None = None,
) -> dict[str, object]:
    product_store = store or ChromaProductStore()
    indexed_ids = set(product_store.indexed_product_ids())
    indexed_hashes = _indexed_content_hashes(product_store.indexed_product_metadata())
    with session_factory() as db:
        products = ProductRepository(db).get_all()
        db_ids = {product.id for product in products}
        db_hashes = {product.id: _product_content_hash(product) for product in products}

    expected_ids = set(expected_product_ids or db_ids)
    missing_in_index = sorted(expected_ids - indexed_ids)
    stale_in_index = sorted(indexed_ids - db_ids)
    content_stale_in_index = _content_stale_ids(expected_ids, indexed_hashes, db_hashes)
    return {
        "ok": not missing_in_index and not stale_in_index and not content_stale_in_index,
        "profile": profile,
        "collection_count": product_store.count(),
        "db_product_count": len(db_ids),
        "expected_product_count": len(expected_ids),
        "indexed_product_ids": sorted(indexed_ids),
        "missing_in_index": missing_in_index,
        "stale_in_index": stale_in_index,
        "content_stale_in_index": content_stale_in_index,
    }


def _build_product_docs(product) -> list[dict]:
    docs = []
    indexed_at = datetime.now(UTC).isoformat()
    content_hash = _product_content_hash(product)
    for chunk in build_product_chunks(product):
        chunk_type = chunk["chunk_type"]
        docs.append(
            {
                "id": f"product_{product.id}:{chunk_type}",
                "text": chunk["text"],
                "metadata": {
                    **_product_metadata(product),
                    "chunk_type": chunk_type,
                    "field_path": chunk["field_path"],
                    "content_hash": content_hash,
                    "indexed_at": indexed_at,
                },
            }
        )
    return docs


def _product_metadata(product) -> dict:
    return {
        "product_id": product.id,
        "name": product.name,
        "category": product.category,
        "brand": product.brand,
        "sku": product.sku,
        "platform": product.platform,
        "product_url": product.product_url,
        "price": _to_float(product.price),
        "stock_status": product.stock_status,
    }


def _product_content_hash(product) -> str:
    payload = {
        "chunks": build_product_chunks(product),
        "metadata": _product_metadata(product),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _indexed_content_hashes(metadatas: list[dict]) -> dict[int, set[str]]:
    hashes_by_product_id: dict[int, set[str]] = {}
    for metadata in metadatas:
        product_id = metadata.get("product_id")
        if product_id is None:
            continue
        content_hash = str(metadata.get("content_hash") or "")
        hashes_by_product_id.setdefault(int(product_id), set()).add(content_hash)
    return hashes_by_product_id


def _content_stale_ids(
    expected_ids: set[int],
    indexed_hashes: dict[int, set[str]],
    db_hashes: dict[int, str],
) -> list[int]:
    stale_ids = []
    for product_id in sorted(expected_ids):
        db_hash = db_hashes.get(product_id)
        index_hashes = indexed_hashes.get(product_id)
        if db_hash is None or index_hashes is None:
            continue
        if index_hashes != {db_hash}:
            stale_ids.append(product_id)
    return stale_ids


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _iter_batches(docs: list[dict], batch_size: int) -> list[list[dict]]:
    size = max(1, batch_size)
    return [docs[index : index + size] for index in range(0, len(docs), size)]
