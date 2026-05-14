"""Build product vector index."""

from __future__ import annotations

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
) -> dict[str, int]:
    product_store = store or ChromaProductStore()
    product_store.reset()

    with session_factory() as db:
        products = ProductRepository(db).get_all()
        docs = [
            {
                "id": f"product_{product.id}",
                "text": build_product_text(product),
                "metadata": {
                    "product_id": product.id,
                    "category": product.category,
                    "price": _to_float(product.price),
                },
            }
            for product in products
        ]

    if docs:
        product_store.add_documents(docs)

    return {"indexed": len(docs)}


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def main() -> None:
    result = build_vector_index()
    print(f"Indexed {result['indexed']} products.")


if __name__ == "__main__":
    main()
