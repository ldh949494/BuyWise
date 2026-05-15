"""Build product vector index."""

from __future__ import annotations

import argparse
from decimal import Decimal
from typing import Callable

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
        products = repo.get_by_ids(product_ids) if product_ids else repo.get_all()
        docs = [
            {
                "id": f"product_{product.id}",
                "text": build_product_text(product),
                "metadata": {
                    "product_id": product.id,
                    "name": product.name,
                    "category": product.category,
                    "price": _to_float(product.price),
                },
            }
            for product in products
        ]

    for batch in _iter_batches(docs, batch_size):
        product_store.add_documents(batch)

    return {"indexed": len(docs), "mode": mode, "deleted_collection": deleted_collection}


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _iter_batches(docs: list[dict], batch_size: int) -> list[list[dict]]:
    size = max(1, batch_size)
    return [docs[index : index + size] for index in range(0, len(docs), size)]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build or update the product vector index.")
    parser.add_argument(
        "--mode",
        choices=["rebuild", "upsert"],
        default="rebuild",
        help="Use rebuild to reset the collection first, or upsert to update matching products.",
    )
    parser.add_argument(
        "--product-id",
        action="append",
        type=int,
        default=[],
        help="Product ID to upsert. Can be passed multiple times.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of product documents to write per batch.",
    )
    args = parser.parse_args()

    result = build_vector_index(
        mode=args.mode,
        product_ids=args.product_id,
        batch_size=args.batch_size,
    )
    print(
        f"Indexed {result['indexed']} products "
        f"(mode={result['mode']}, deleted_collection={result['deleted_collection']})."
    )


if __name__ == "__main__":
    main()
