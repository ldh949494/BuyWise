"""Reset catalog and catalog-derived beta data."""

from __future__ import annotations

import argparse
import json
from typing import Any

from sqlalchemy import text

from app.core.database import SessionLocal

TABLES = [
    "recommendations",
    "reviews",
    "order_items",
    "orders",
    "price_history",
    "chat_messages",
    "chat_sessions",
    "products",
]


def reset_catalog(confirm_delete: bool = False) -> dict[str, Any]:
    with SessionLocal() as db:
        before = _table_counts(db)
        if not confirm_delete:
            return {"deleted": False, "before": before, "after": before}

        for table in TABLES:
            db.execute(text(f"DELETE FROM {table}"))
        _reset_product_autoincrement(db)
        db.commit()
        return {"deleted": True, "before": before, "after": _table_counts(db)}


def _table_counts(db) -> dict[str, int]:
    return {table: int(db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()) for table in TABLES}


def _reset_product_autoincrement(db) -> None:
    try:
        db.execute(text("ALTER TABLE products AUTO_INCREMENT = 1"))
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset catalog and catalog-derived data before beta import.")
    parser.add_argument("--confirm-delete", action="store_true", help="Actually delete data. Omit for dry-run counts.")
    args = parser.parse_args()
    print(json.dumps(reset_catalog(confirm_delete=args.confirm_delete), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
