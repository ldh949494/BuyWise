"""Run detailed readiness checks for deployment verification."""

from __future__ import annotations

import argparse
import json

from app.core.dependencies import build_app_container


def main() -> None:
    args = _parse_args()
    container = build_app_container()
    try:
        report = container.readiness_service.validate_readiness(
            include_details=True,
            expected_active_products=args.expected_active_products,
        )
    finally:
        container.close()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "ready":
        raise SystemExit(1)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run detailed BuyWise deployment readiness checks.")
    parser.add_argument(
        "--expected-active-products",
        type=int,
        help="Fail when the active product count does not exactly match this value.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
