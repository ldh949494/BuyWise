"""Validate a closed beta product CSV without writing to the database."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from app.scripts.import_products import validate_product_rows

DEFAULT_CSV_PATH = Path(__file__).resolve().parents[2] / "data" / "beta-catalog.csv"
EXPECTED_COLUMNS = [
    "sku",
    "name",
    "category",
    "brand",
    "price",
    "original_price",
    "platform",
    "product_url",
    "image_url",
    "image_urls",
    "rating",
    "sales",
    "description",
    "specs",
    "tags",
    "suitable_scene",
    "stock",
    "stock_status",
    "review_summary",
]
EXPECTED_CATEGORIES = {"机械键盘", "蓝牙耳机", "台灯", "充电宝", "双肩包"}
ALLOWED_TAGS = {
    "性价比",
    "轻便",
    "耐用",
    "高颜值",
    "送礼",
    "学生党",
    "办公",
    "便携",
    "低噪音",
    "无线",
    "三模",
    "蓝牙",
    "热插拔",
    "紧凑布局",
    "写代码",
    "长续航",
    "降噪",
    "通话清晰",
    "低延迟",
    "佩戴舒适",
    "运动",
    "通勤",
    "入耳式",
    "护眼",
    "无频闪",
    "高显色",
    "无级调光",
    "小巧",
    "阅读",
    "备考",
    "宿舍",
    "快充",
    "USB-C",
    "轻薄",
    "大容量",
    "小容量",
    "自带线",
    "旅行",
    "应急",
    "电脑仓",
    "防泼水",
    "上课",
    "分区收纳",
    "简约",
}
ALLOWED_SCENES = {"宿舍", "通勤", "办公", "学习", "写代码", "阅读", "旅行", "送礼", "应急", "备考", "上课", "运动"}
SKU_RE = re.compile(r"^beta-[a-z0-9]+(?:-[a-z0-9]+)*$")


def validate_beta_catalog(csv_path: str | Path = DEFAULT_CSV_PATH, expected_per_category: int = 10) -> dict[str, Any]:
    path = Path(csv_path)
    errors: list[str] = []

    try:
        rows, fieldnames = _read_csv(path)
    except FileNotFoundError:
        return {"ok": False, "path": str(path), "rows": 0, "errors": [f"CSV not found: {path}"]}

    errors.extend(_validate_import_shape(rows, fieldnames))
    errors.extend(_validate_category_counts(rows, expected_per_category))
    for line_number, row in enumerate(rows, start=2):
        errors.extend(_validate_row_taxonomy(row, line_number))

    return {
        "ok": not errors,
        "path": str(path),
        "rows": len(rows),
        "category_counts": dict(Counter(row.get("category", "").strip() for row in rows)),
        "errors": errors,
    }


def _read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader), reader.fieldnames or []


def _validate_import_shape(rows: list[dict[str, str]], fieldnames: list[str]) -> list[str]:
    errors: list[str] = []
    if fieldnames != EXPECTED_COLUMNS:
        errors.append(f"CSV header must match template columns exactly: {EXPECTED_COLUMNS}")
    try:
        validate_product_rows(rows, require_real_assets=True)
    except ValueError as exc:
        errors.append(str(exc))
    return errors


def _validate_category_counts(rows: list[dict[str, str]], expected_per_category: int) -> list[str]:
    errors: list[str] = []
    counts = Counter(row.get("category", "").strip() for row in rows)
    seen_categories = set(counts)
    unknown_categories = sorted(category for category in seen_categories if category not in EXPECTED_CATEGORIES)
    missing_categories = sorted(EXPECTED_CATEGORIES - seen_categories)

    if unknown_categories:
        errors.append(f"Unknown categories: {unknown_categories}")
    if missing_categories:
        errors.append(f"Missing categories: {missing_categories}")

    for category in sorted(EXPECTED_CATEGORIES):
        count = counts.get(category, 0)
        if count != expected_per_category:
            errors.append(f"Category {category} must contain {expected_per_category} SKUs, found {count}.")
        category_rows = [row for row in rows if row.get("category", "").strip() == category]
        errors.extend(_validate_category_diversity(category, category_rows, expected_per_category))
    return errors


def _validate_category_diversity(category: str, rows: list[dict[str, str]], expected_per_category: int) -> list[str]:
    if expected_per_category < 10 or len(rows) < 10:
        return []

    errors: list[str] = []
    brand_counts = Counter(str(row.get("brand") or "").strip() for row in rows)
    brand_counts.pop("", None)
    if len(brand_counts) < 4:
        errors.append(f"Category {category} must include at least 4 brands/stores, found {len(brand_counts)}.")

    overrepresented = sorted(brand for brand, count in brand_counts.items() if count > 3)
    if overrepresented:
        errors.append(f"Category {category} has brands/stores over the max 3 SKU limit: {overrepresented}.")

    price_bands = _category_price_bands(rows)
    if len(price_bands) < 3:
        errors.append(f"Category {category} must cover low, mid, and high price bands.")
    return errors


def _category_price_bands(rows: list[dict[str, str]]) -> set[str]:
    prices: list[Decimal] = []
    for row in rows:
        try:
            prices.append(Decimal(str(row.get("price") or "").strip()))
        except (InvalidOperation, ValueError):
            continue
    if not prices:
        return set()

    low = min(prices)
    high = max(prices)
    if low == high:
        return {"single"}

    one_third = low + (high - low) / Decimal("3")
    two_thirds = low + (high - low) * Decimal("2") / Decimal("3")
    bands = set()
    for price in prices:
        if price <= one_third:
            bands.add("low")
        elif price <= two_thirds:
            bands.add("mid")
        else:
            bands.add("high")
    return bands


def _validate_row_taxonomy(row: dict[str, str], line_number: int) -> list[str]:
    errors: list[str] = []
    sku = str(row.get("sku") or "").strip()
    if not SKU_RE.fullmatch(sku):
        errors.append(f"CSV row {line_number} sku must match beta-<slug> format.")

    errors.extend(_validate_json_list_field(row, line_number, "tags", ALLOWED_TAGS, 4, 8))
    errors.extend(_validate_json_list_field(row, line_number, "suitable_scene", ALLOWED_SCENES, 2, 5))
    errors.extend(_validate_json_object_field(row, line_number, "specs"))

    review_summary = str(row.get("review_summary") or "").strip()
    if not review_summary:
        errors.append(f"CSV row {line_number} review_summary is required.")
    return errors


def _validate_json_list_field(
    row: dict[str, str],
    line_number: int,
    field: str,
    allowed_values: set[str],
    min_items: int,
    max_items: int,
) -> list[str]:
    errors: list[str] = []
    value = str(row.get(field) or "").strip()
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return [f"CSV row {line_number} {field} must be valid JSON."]

    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        return [f"CSV row {line_number} {field} must be a JSON string list."]

    if not min_items <= len(parsed) <= max_items:
        errors.append(f"CSV row {line_number} {field} must contain {min_items}-{max_items} items.")

    unknown_values = sorted(set(parsed) - allowed_values)
    if unknown_values:
        errors.append(f"CSV row {line_number} {field} contains values outside taxonomy: {unknown_values}")
    return errors


def _validate_json_object_field(row: dict[str, str], line_number: int, field: str) -> list[str]:
    value = str(row.get(field) or "").strip()
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return [f"CSV row {line_number} {field} must be valid JSON."]
    if not isinstance(parsed, dict):
        return [f"CSV row {line_number} {field} must be a JSON object."]
    return []


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a closed beta product CSV without importing it.")
    parser.add_argument("--csv", default=str(DEFAULT_CSV_PATH), help="Path to beta catalog CSV file.")
    parser.add_argument(
        "--expected-per-category",
        type=int,
        default=10,
        help="Expected SKU count for each closed beta category.",
    )
    args = parser.parse_args()

    report = validate_beta_catalog(args.csv, expected_per_category=args.expected_per_category)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
