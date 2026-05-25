"""Import product data from CSV into the products table."""

from __future__ import annotations

import argparse
import csv
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services.product_service import IndexUpdater, ProductService

DEFAULT_CSV_PATH = Path(__file__).resolve().parents[2] / "data" / "products.csv"
JSON_FIELDS = {"specs", "tags", "suitable_scene", "image_urls"}
DECIMAL_FIELDS = {"price", "original_price", "rating"}
INT_FIELDS = {"sales", "stock"}
REQUIRED_FIELDS = {"sku", "name", "category", "price", "tags"}
PLACEHOLDER_HOSTS = {"example.com", "example.test", "localhost", "127.0.0.1"}


def parse_product_row(row: dict[str, str]) -> dict[str, Any]:
    product_data: dict[str, Any] = {}
    for key, value in row.items():
        if value is None or value == "":
            product_data[key] = None
        elif key in JSON_FIELDS:
            product_data[key] = json.loads(value)
        elif key in DECIMAL_FIELDS:
            product_data[key] = Decimal(value)
        elif key in INT_FIELDS:
            product_data[key] = int(value)
        else:
            product_data[key] = value
    return product_data


def validate_product_rows(rows: list[dict[str, str]], *, require_real_assets: bool = False) -> None:
    seen_skus = set()
    for index, row in enumerate(rows, start=2):
        missing = [field for field in REQUIRED_FIELDS if not str(row.get(field) or "").strip()]
        if missing:
            raise ValueError(f"CSV row {index} missing required fields: {missing}")
        sku = row["sku"].strip()
        if sku in seen_skus:
            raise ValueError(f"CSV row {index} duplicates sku: {sku}")
        seen_skus.add(sku)
        _validate_price(row["price"], index)
        _validate_tags(row["tags"], index)
        if require_real_assets:
            _validate_real_catalog_fields(row, index)


def import_products(
    csv_path: str | Path = DEFAULT_CSV_PATH,
    session_factory: Callable[[], Session] = SessionLocal,
    index_updater: IndexUpdater | None = None,
    require_real_assets: bool = False,
) -> dict[str, int]:
    path = Path(csv_path)
    inserted = 0
    updated = 0

    with path.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    validate_product_rows(rows, require_real_assets=require_real_assets)

    with session_factory() as db:
        service = ProductService(db, index_updater=index_updater)
        for row in rows:
            product_data = parse_product_row(row)
            _, was_inserted = service.update_product_by_sku(product_data)
            if was_inserted:
                inserted += 1
            else:
                updated += 1

    return {"inserted": inserted, "updated": updated, "failed": 0}


def _validate_price(value: str, line_number: int) -> None:
    try:
        price = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"CSV row {line_number} has invalid price.") from exc
    if price < 0:
        raise ValueError(f"CSV row {line_number} has negative price.")


def _validate_tags(value: str, line_number: int) -> None:
    try:
        tags = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"CSV row {line_number} has invalid tags JSON.") from exc
    if not isinstance(tags, list) or not tags:
        raise ValueError(f"CSV row {line_number} tags must be a non-empty JSON list.")


def _validate_real_catalog_fields(row: dict[str, str], line_number: int) -> None:
    product_url = str(row.get("product_url") or "").strip()
    if not _is_real_url(product_url):
        raise ValueError(f"CSV row {line_number} product_url must be a real http(s) URL.")
    image_urls = _image_urls(row, line_number)
    if not image_urls or any(not _is_real_url(url) for url in image_urls):
        raise ValueError(f"CSV row {line_number} must include real http(s) image URL(s).")
    stock_status = str(row.get("stock_status") or "").strip()
    stock = str(row.get("stock") or "").strip()
    if not stock_status and not stock:
        raise ValueError(f"CSV row {line_number} must include stock or stock_status.")


def _image_urls(row: dict[str, str], line_number: int) -> list[str]:
    image_url = str(row.get("image_url") or "").strip()
    raw_image_urls = str(row.get("image_urls") or "").strip()
    urls = [image_url] if image_url else []
    if raw_image_urls:
        try:
            parsed = json.loads(raw_image_urls)
        except json.JSONDecodeError as exc:
            raise ValueError(f"CSV row {line_number} has invalid image_urls JSON.") from exc
        if not isinstance(parsed, list):
            raise ValueError(f"CSV row {line_number} image_urls must be a JSON list.")
        urls.extend(str(item).strip() for item in parsed if str(item).strip())
    return urls


def _is_real_url(value: str) -> bool:
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    return parsed.scheme in {"http", "https"} and bool(host) and host not in PLACEHOLDER_HOSTS


def main() -> None:
    parser = argparse.ArgumentParser(description="Import demo product data into MySQL.")
    parser.add_argument(
        "--csv",
        default=str(DEFAULT_CSV_PATH),
        help="Path to products CSV file.",
    )
    parser.add_argument(
        "--require-real-assets",
        action="store_true",
        help="Require real product URLs, image URLs, and stock fields for closed beta catalogs.",
    )
    args = parser.parse_args()

    result = import_products(args.csv, require_real_assets=args.require_real_assets)
    print(
        f"Inserted {result['inserted']} products, "
        f"updated {result['updated']} products, failed {result['failed']} rows."
    )


if __name__ == "__main__":
    main()
