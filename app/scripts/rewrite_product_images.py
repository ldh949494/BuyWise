"""Rewrite database product image URLs from a maintained catalog CSV."""

from __future__ import annotations

import argparse
import csv
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.product import Product
from app.scripts.job_artifacts import run_job_with_artifact

DEFAULT_SOURCE_PATH = Path(__file__).resolve().parents[2] / "data" / "products.csv"


@dataclass
class RewriteSummary:
    source_rows: int = 0
    products_seen: int = 0
    products_updated: int = 0
    products_unchanged: int = 0
    missing_skus: list[str] = field(default_factory=list)
    updates: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_rows": self.source_rows,
            "products_seen": self.products_seen,
            "products_updated": self.products_updated,
            "products_unchanged": self.products_unchanged,
            "missing_skus": self.missing_skus,
            "updates": self.updates,
        }


def rewrite_product_images(
    *,
    source_path: str | Path = DEFAULT_SOURCE_PATH,
    session_factory: Callable[[], Session] = SessionLocal,
    dry_run: bool = True,
) -> RewriteSummary:
    assets = _load_assets(Path(source_path))
    summary = RewriteSummary(source_rows=len(assets))
    with session_factory() as db:
        _rewrite_images(db, assets=assets, summary=summary, dry_run=dry_run)
        if dry_run:
            db.rollback()
        else:
            db.commit()
    return summary


def _load_assets(source_path: Path) -> dict[str, dict[str, Any]]:
    with source_path.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assets: dict[str, dict[str, Any]] = {}
    for row in rows:
        sku = str(row.get("sku") or "").strip()
        if not sku:
            continue
        image_url = str(row.get("image_url") or "").strip()
        image_urls = _parse_image_urls(row.get("image_urls"), image_url)
        assets[sku] = {"image_url": image_url, "image_urls": image_urls}
    return assets


def _parse_image_urls(raw_value: Any, image_url: str) -> list[str]:
    if isinstance(raw_value, list):
        values = [str(value).strip() for value in raw_value if str(value).strip()]
    else:
        value = str(raw_value or "").strip()
        if not value:
            values = []
        else:
            parsed = json.loads(value)
            if not isinstance(parsed, list):
                raise ValueError("image_urls must be a JSON list.")
            values = [str(item).strip() for item in parsed if str(item).strip()]
    if image_url and image_url not in values:
        values.insert(0, image_url)
    return values


def _rewrite_images(
    db: Session,
    *,
    assets: dict[str, dict[str, Any]],
    summary: RewriteSummary,
    dry_run: bool,
) -> None:
    for sku, asset in sorted(assets.items()):
        product = db.query(Product).filter(Product.sku == sku).first()
        if product is None:
            summary.missing_skus.append(sku)
            continue
        summary.products_seen += 1
        previous = {"image_url": product.image_url, "image_urls": product.image_urls or []}
        next_values = {"image_url": asset["image_url"], "image_urls": asset["image_urls"]}
        if previous == next_values:
            summary.products_unchanged += 1
            continue
        summary.products_updated += 1
        summary.updates.append(
            {
                "sku": sku,
                "product_id": product.id,
                "previous": previous,
                "next": next_values,
            }
        )
        if not dry_run:
            product.image_url = next_values["image_url"]
            product.image_urls = next_values["image_urls"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Rewrite product image URLs from a maintained catalog CSV.")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE_PATH), help="CSV with sku, image_url, and image_urls columns.")
    parser.add_argument("--apply", action="store_true", help="Write image URL updates to the database.")
    parser.add_argument("--artifact-json", help="Optional path for a machine-readable job artifact.")
    args = parser.parse_args()

    inputs = {"source": args.source, "apply": args.apply}
    summary = run_job_with_artifact(
        job_name="rewrite_product_images",
        inputs=inputs,
        artifact_path=args.artifact_json,
        action=lambda: rewrite_product_images(source_path=args.source, dry_run=not args.apply).as_dict(),
    )
    mode = "apply" if args.apply else "dry-run"
    print(f"{mode}: {summary}")


if __name__ == "__main__":
    main()
