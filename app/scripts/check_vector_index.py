"""Check product vector index health."""

from __future__ import annotations

import argparse
import json

from app.scripts.evaluate_rag import known_seed_product_ids
from app.services.product_index_service import validate_vector_index_health


def main() -> None:
    args = _parse_args()
    expected_ids = sorted(known_seed_product_ids(args.profile)) if args.profile else None
    report = validate_vector_index_health(expected_product_ids=expected_ids, profile=args.profile)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        raise SystemExit(1)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check BuyWise product vector index health.")
    parser.add_argument(
        "--profile",
        choices=["android-contract", "demo"],
        help="Optional seed profile whose product IDs should be present in the index.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
