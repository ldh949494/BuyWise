"""Import product data from CSV into the products table."""

from __future__ import annotations

import argparse
import csv
import json
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.product import Product

DEFAULT_CSV_PATH = Path(__file__).resolve().parents[2] / "data" / "products.csv"
JSON_FIELDS = {"specs", "tags", "suitable_scene", "image_urls"}
DECIMAL_FIELDS = {"price", "original_price", "rating"}
INT_FIELDS = {"sales", "stock"}


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


def import_products(
    csv_path: str | Path = DEFAULT_CSV_PATH,
    session_factory: Callable[[], Session] = SessionLocal,
) -> dict[str, int]:
    path = Path(csv_path)
    inserted = 0
    skipped = 0

    with path.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))

    with session_factory() as db:
        existing_names = set(db.scalars(select(Product.name)).all())
        for row in rows:
            product_data = parse_product_row(row)
            name = product_data["name"]
            if name in existing_names:
                skipped += 1
                continue

            db.add(Product(**product_data))
            existing_names.add(name)
            inserted += 1

        db.commit()

    return {"inserted": inserted, "skipped": skipped}


def main() -> None:
    parser = argparse.ArgumentParser(description="Import demo product data into MySQL.")
    parser.add_argument(
        "--csv",
        default=str(DEFAULT_CSV_PATH),
        help="Path to products CSV file.",
    )
    args = parser.parse_args()

    result = import_products(args.csv)
    print(f"Inserted {result['inserted']} products, skipped {result['skipped']} duplicates.")


if __name__ == "__main__":
    main()
