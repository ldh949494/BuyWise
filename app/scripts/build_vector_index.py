"""Build product vector index."""

from __future__ import annotations

import argparse

from app.services.product_index_service import build_vector_index, update_product_index


def main() -> None:
    args = _parse_args()
    result = build_vector_index(
        mode=args.mode,
        product_ids=args.product_id,
        batch_size=args.batch_size,
    )
    print(
        f"Indexed {result['indexed']} products "
        f"(mode={result['mode']}, deleted_collection={result['deleted_collection']})."
    )


def _parse_args() -> argparse.Namespace:
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
    return parser.parse_args()


if __name__ == "__main__":
    main()
