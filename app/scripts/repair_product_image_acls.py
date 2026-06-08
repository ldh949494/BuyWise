"""Repair Tencent COS ACLs for product images referenced by catalogs and seed data."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from app.core.config import settings
from app.integrations.cos_storage_client import TencentCosStorageClient
from app.scripts.demo_desktop_products import DEMO_DESKTOP_PRODUCTS
from app.scripts.demo_products import DEMO_SHOWCASE_PRODUCTS
from app.scripts.job_artifacts import run_job_with_artifact
from app.scripts.seed_products import ANDROID_CONTRACT_PRODUCTS

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CSV_PATHS = [ROOT / "data" / "products.csv", ROOT / "data" / "beta-catalog.csv"]


@dataclass
class RepairAclSummary:
    urls_seen: int = 0
    keys_seen: int = 0
    keys_repaired: int = 0
    keys_skipped: int = 0
    keys_failed: int = 0
    failures: list[dict[str, str]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "urls_seen": self.urls_seen,
            "keys_seen": self.keys_seen,
            "keys_repaired": self.keys_repaired,
            "keys_skipped": self.keys_skipped,
            "keys_failed": self.keys_failed,
        }
        if self.failures:
            payload["failures"] = self.failures
        return payload


def repair_product_image_acls(
    *,
    csv_paths: list[str | Path] | None = None,
    include_seed_profiles: bool = True,
    dry_run: bool = True,
    client: Any | None = None,
) -> RepairAclSummary:
    summary = RepairAclSummary()
    urls = _collect_urls(csv_paths or DEFAULT_CSV_PATHS, include_seed_profiles=include_seed_profiles)
    summary.urls_seen = len(urls)
    keys = sorted(_cos_product_image_keys(urls))
    summary.keys_seen = len(keys)
    storage_client = client or (None if dry_run else TencentCosStorageClient().client)
    for key in keys:
        if dry_run:
            summary.keys_skipped += 1
            continue
        try:
            storage_client.put_object_acl(Bucket=settings.cos_bucket, Key=key, ACL="public-read")
            summary.keys_repaired += 1
        except Exception as exc:
            summary.keys_failed += 1
            summary.failures.append({"key": key, "error": f"{type(exc).__name__}: {exc}"})
    return summary


def _collect_urls(csv_paths: list[str | Path], *, include_seed_profiles: bool) -> set[str]:
    urls: set[str] = set()
    for csv_path in csv_paths:
        urls.update(_catalog_urls(Path(csv_path)))
    if include_seed_profiles:
        for product in [*ANDROID_CONTRACT_PRODUCTS, *DEMO_SHOWCASE_PRODUCTS, *DEMO_DESKTOP_PRODUCTS]:
            urls.update(_product_urls(product))
    return urls


def _catalog_urls(path: Path) -> set[str]:
    with path.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    urls: set[str] = set()
    for row in rows:
        urls.update(_product_urls(row))
    return urls


def _product_urls(product: dict[str, Any]) -> set[str]:
    urls = set()
    image_url = str(product.get("image_url") or "").strip()
    if image_url:
        urls.add(image_url)
    image_urls = product.get("image_urls")
    if isinstance(image_urls, list):
        urls.update(str(url).strip() for url in image_urls if str(url).strip())
    else:
        raw_value = str(image_urls or "").strip()
        if raw_value:
            parsed = json.loads(raw_value)
            if isinstance(parsed, list):
                urls.update(str(url).strip() for url in parsed if str(url).strip())
    return urls


def _cos_product_image_keys(urls: set[str]) -> set[str]:
    expected_host = f"{settings.cos_bucket}.cos.{settings.cos_region}.myqcloud.com".lower()
    keys = set()
    for url in urls:
        parsed = urlparse(url)
        if (parsed.hostname or "").lower() != expected_host:
            continue
        key = unquote(parsed.path.lstrip("/"))
        if key.startswith("product-images/"):
            keys.add(key)
    return keys


def main() -> None:
    parser = argparse.ArgumentParser(description="Repair public-read ACLs for product images stored in Tencent COS.")
    parser.add_argument("--csv", action="append", dest="csv_paths", help="Catalog CSV to scan. Can be repeated.")
    parser.add_argument("--skip-seed-profiles", action="store_true", help="Only scan CSV files.")
    parser.add_argument("--apply", action="store_true", help="Write public-read ACLs to matching COS objects.")
    parser.add_argument("--artifact-json", help="Optional path for a machine-readable job artifact.")
    args = parser.parse_args()

    inputs = {"csv": args.csv_paths, "include_seed_profiles": not args.skip_seed_profiles, "apply": args.apply}
    summary = run_job_with_artifact(
        job_name="repair_product_image_acls",
        inputs=inputs,
        artifact_path=args.artifact_json,
        action=lambda: repair_product_image_acls(
            csv_paths=args.csv_paths,
            include_seed_profiles=not args.skip_seed_profiles,
            dry_run=not args.apply,
        ).as_dict(),
    )
    mode = "apply" if args.apply else "dry-run"
    print(f"{mode}: {summary}")


if __name__ == "__main__":
    main()
