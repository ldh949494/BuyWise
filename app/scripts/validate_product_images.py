"""Validate product image URLs used by catalog and seed data."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from app.scripts.demo_broad_products import DEMO_BROAD_PRODUCTS
from app.scripts.demo_desktop_products import DEMO_DESKTOP_PRODUCTS
from app.scripts.demo_products import DEMO_SHOWCASE_PRODUCTS
from app.scripts.seed_products import ANDROID_CONTRACT_PRODUCTS

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CSV_PATH = ROOT / "data" / "products.csv"
PLACEHOLDER_HOSTS = {"example.com", "example.test", "localhost", "127.0.0.1"}
DEFAULT_COS_HOST = "buywise-1392410096.cos.ap-guangzhou.myqcloud.com"


def validate_product_images(
    *,
    csv_paths: list[str | Path] | None = None,
    include_seed_profiles: bool = True,
    require_cos_host: str = DEFAULT_COS_HOST,
    require_unique_image_urls: bool = False,
    check_http: bool = False,
    min_image_bytes: int | None = None,
    require_unique_http_etags: bool = False,
) -> dict[str, Any]:
    records = _collect_records(csv_paths or [DEFAULT_CSV_PATH], include_seed_profiles=include_seed_profiles)
    errors = _validate_records(
        records,
        require_cos_host=require_cos_host,
        require_unique_image_urls=require_unique_image_urls,
        check_http=check_http,
        min_image_bytes=min_image_bytes,
        require_unique_http_etags=require_unique_http_etags,
    )
    return {
        "ok": not errors,
        "records": len(records),
        "sources": sorted({record["source"] for record in records}),
        "unique_image_urls": len({record["image_url"] for record in records if record["image_url"]}),
        "errors": errors,
    }


def _collect_records(csv_paths: list[str | Path], *, include_seed_profiles: bool) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for csv_path in csv_paths:
        records.extend(_csv_records(Path(csv_path)))
    if include_seed_profiles:
        records.extend(_seed_records("android-contract", ANDROID_CONTRACT_PRODUCTS))
        records.extend(_seed_records("demo-showcase", DEMO_SHOWCASE_PRODUCTS))
        records.extend(_seed_records("demo-desktop", DEMO_DESKTOP_PRODUCTS))
        records.extend(_seed_records("demo-broad", DEMO_BROAD_PRODUCTS))
    return records


def _csv_records(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    return [_record_from_row(row, source=str(path)) for row in rows]


def _seed_records(source: str, products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_record_from_row(product, source=source) for product in products]


def _record_from_row(row: dict[str, Any], *, source: str) -> dict[str, Any]:
    image_url = str(row.get("image_url") or "").strip()
    return {
        "source": source,
        "sku": str(row.get("sku") or "").strip(),
        "name": str(row.get("name") or "").strip(),
        "category": str(row.get("category") or "").strip(),
        "product_url": str(row.get("product_url") or "").strip(),
        "image_url": image_url,
        "image_urls": _image_urls(row.get("image_urls"), image_url),
    }


def _image_urls(value: Any, image_url: str) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    raw_value = str(value or "").strip()
    if not raw_value:
        return [image_url] if image_url else []
    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item).strip() for item in parsed if str(item).strip()]


def _validate_records(
    records: list[dict[str, Any]],
    *,
    require_cos_host: str,
    require_unique_image_urls: bool,
    check_http: bool,
    min_image_bytes: int | None,
    require_unique_http_etags: bool,
) -> list[str]:
    errors: list[str] = []
    http_metadata: list[dict[str, Any]] = []
    for index, record in enumerate(records, start=1):
        record_errors, metadata = _validate_record(
            record,
            index=index,
            require_cos_host=require_cos_host,
            check_http=check_http,
            min_image_bytes=min_image_bytes,
        )
        errors.extend(record_errors)
        if metadata:
            http_metadata.append(metadata)
    if require_unique_image_urls:
        errors.extend(_duplicate_image_errors(records))
    if require_unique_http_etags:
        errors.extend(_duplicate_http_etag_errors(http_metadata))
    return errors


def _validate_record(
    record: dict[str, Any],
    *,
    index: int,
    require_cos_host: str,
    check_http: bool,
    min_image_bytes: int | None,
) -> tuple[list[str], dict[str, Any] | None]:
    label = _record_label(record, index)
    errors: list[str] = []
    if not record["sku"]:
        errors.append(f"{label} sku is required.")
    if not record["name"]:
        errors.append(f"{label} name is required.")
    errors.extend(_validate_url(record["product_url"], label=label, field="product_url", require_cos_host=None))
    errors.extend(_validate_url(record["image_url"], label=label, field="image_url", require_cos_host=require_cos_host))
    if not record["image_urls"]:
        errors.append(f"{label} image_urls must contain at least the main image URL.")
    elif record["image_url"] and record["image_url"] not in record["image_urls"]:
        errors.append(f"{label} image_urls must contain image_url.")
    for image_url in record["image_urls"]:
        errors.extend(_validate_url(image_url, label=label, field="image_urls", require_cos_host=require_cos_host))
    http_errors, metadata = _validate_record_http_image(
        record,
        label=label,
        check_http=check_http,
        min_image_bytes=min_image_bytes,
    )
    errors.extend(http_errors)
    return errors, metadata


def _validate_record_http_image(
    record: dict[str, Any],
    *,
    label: str,
    check_http: bool,
    min_image_bytes: int | None,
) -> tuple[list[str], dict[str, Any] | None]:
    if not check_http or not record["image_url"]:
        return [], None
    return _validate_http_image(
        record["image_url"],
        label=label,
        min_image_bytes=min_image_bytes,
    )


def _validate_url(
    value: str,
    *,
    label: str,
    field: str,
    require_cos_host: str | None,
) -> list[str]:
    if not value:
        return [f"{label} {field} is required."]
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"} or not host:
        return [f"{label} {field} must be an absolute http(s) URL."]
    if host in PLACEHOLDER_HOSTS:
        return [f"{label} {field} must not use placeholder host {host}."]
    if require_cos_host and host != require_cos_host.lower():
        return [f"{label} {field} must use COS host {require_cos_host}."]
    return []


def _validate_http_image(
    value: str,
    *,
    label: str,
    min_image_bytes: int | None,
) -> tuple[list[str], dict[str, Any] | None]:
    request = Request(value, headers={"User-Agent": "BuyWiseImageValidator/1.0"})
    try:
        with urlopen(request, timeout=10) as response:  # noqa: S310 - URL comes from maintained catalog data.
            content_type = response.headers.get("content-type", "")
            content_length = response.headers.get("content-length", "")
            etag = response.headers.get("etag", "")
    except Exception as exc:
        return [f"{label} image_url is not reachable: {type(exc).__name__}: {exc}"], None
    if not content_type.lower().startswith("image/"):
        return [f"{label} image_url must return image content, got {content_type or 'unknown'}."], None
    errors = []
    byte_count = _parse_content_length(content_length)
    if min_image_bytes is not None and byte_count is not None and byte_count < min_image_bytes:
        errors.append(f"{label} image_url is too small: {byte_count} bytes, minimum is {min_image_bytes}.")
    metadata = {
        "label": label,
        "url": value,
        "etag": etag.strip('"'),
        "content_length": byte_count,
        "content_type": content_type,
    }
    return errors, metadata


def _parse_content_length(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _duplicate_image_errors(records: list[dict[str, Any]]) -> list[str]:
    image_counts = Counter(record["image_url"] for record in records if record["image_url"])
    errors = []
    for image_url, count in sorted(image_counts.items()):
        if count <= 1:
            continue
        labels = [_record_label(record, index) for index, record in enumerate(records, start=1) if record["image_url"] == image_url]
        errors.append(f"image_url is reused by {count} products: {labels}")
    return errors


def _duplicate_http_etag_errors(metadata: list[dict[str, Any]]) -> list[str]:
    etag_counts = Counter(item["etag"] for item in metadata if item.get("etag"))
    errors = []
    for etag, count in sorted(etag_counts.items()):
        if count <= 1:
            continue
        labels = [item["label"] for item in metadata if item.get("etag") == etag]
        errors.append(f"image content ETag is reused by {count} products: {labels}")
    return errors


def _record_label(record: dict[str, Any], index: int) -> str:
    sku = record.get("sku") or f"row-{index}"
    source = record.get("source") or "unknown"
    return f"{source}:{sku}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate product image URLs used by catalog and seed data.")
    parser.add_argument("--csv", action="append", dest="csv_paths", help="Catalog CSV to validate. Can be repeated.")
    parser.add_argument("--skip-seed-profiles", action="store_true", help="Only validate CSV files.")
    parser.add_argument("--cos-host", default=DEFAULT_COS_HOST, help="Required COS host for image URLs.")
    parser.add_argument("--require-unique-image-urls", action="store_true", help="Fail if multiple products reuse one image URL.")
    parser.add_argument("--check-http", action="store_true", help="Fetch each main image URL and require image content.")
    parser.add_argument("--min-image-bytes", type=int, default=None, help="When --check-http is set, fail images smaller than this.")
    parser.add_argument(
        "--require-unique-http-etags",
        action="store_true",
        help="When --check-http is set, fail if multiple products return the same ETag.",
    )
    args = parser.parse_args()

    report = validate_product_images(
        csv_paths=args.csv_paths,
        include_seed_profiles=not args.skip_seed_profiles,
        require_cos_host=args.cos_host,
        require_unique_image_urls=args.require_unique_image_urls,
        check_http=args.check_http,
        min_image_bytes=args.min_image_bytes,
        require_unique_http_etags=args.require_unique_http_etags,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
