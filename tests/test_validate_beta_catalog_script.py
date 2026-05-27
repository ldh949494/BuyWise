import csv

from app.scripts.validate_beta_catalog import validate_beta_catalog


FIELDNAMES = [
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


def write_catalog(path, rows):
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def row(sku: str, category: str) -> dict[str, str]:
    return {
        "sku": sku,
        "name": f"{category} Product",
        "category": category,
        "brand": "Brand",
        "price": "199.00",
        "original_price": "259.00",
        "platform": "京东",
        "product_url": f"https://shop.real.test/products/{sku}",
        "image_url": f"https://cdn.real.test/images/{sku}.jpg",
        "image_urls": f'["https://cdn.real.test/images/{sku}.jpg"]',
        "rating": "4.7",
        "sales": "120",
        "description": "A real beta catalog product.",
        "specs": '{"feature":"value"}',
        "tags": '["性价比","轻便","办公","便携"]',
        "suitable_scene": '["办公","学习"]',
        "stock": "10",
        "stock_status": "in_stock",
        "review_summary": "人工快照评价摘要完整。",
    }


def test_validate_beta_catalog_accepts_expected_catalog(tmp_path) -> None:
    csv_path = tmp_path / "beta-catalog.csv"
    rows = [
        row("beta-keyboard-keynova-k75", "机械键盘"),
        row("beta-earbuds-soundair-c1", "蓝牙耳机"),
        row("beta-lamp-lightwise-e2", "台灯"),
        row("beta-powerbank-powermax-s10", "充电宝"),
        row("beta-backpack-packlab-city", "双肩包"),
    ]
    write_catalog(csv_path, rows)

    report = validate_beta_catalog(csv_path, expected_per_category=1)

    assert report["ok"] is True
    assert report["rows"] == 5
    assert report["errors"] == []


def test_validate_beta_catalog_reports_taxonomy_and_shape_errors(tmp_path) -> None:
    csv_path = tmp_path / "beta-catalog.csv"
    bad_row = row("JD-1001", "机械键盘")
    bad_row["product_url"] = "https://example.com/products/keyboard"
    bad_row["tags"] = '["静音","无线"]'
    bad_row["suitable_scene"] = '["寝室"]'
    bad_row["review_summary"] = ""
    write_catalog(csv_path, [bad_row])

    report = validate_beta_catalog(csv_path, expected_per_category=1)

    assert report["ok"] is False
    error_text = "\n".join(report["errors"])
    assert "product_url" in error_text
    assert "sku must match beta-<slug>" in error_text
    assert "tags must contain 4-8 items" in error_text
    assert "outside taxonomy" in error_text
    assert "review_summary is required" in error_text


def test_validate_beta_catalog_reports_category_diversity_errors(tmp_path) -> None:
    csv_path = tmp_path / "beta-catalog.csv"
    rows = [row(f"beta-keyboard-same-store-{index}", "机械键盘") for index in range(10)]
    write_catalog(csv_path, rows)

    report = validate_beta_catalog(csv_path, expected_per_category=10)

    assert report["ok"] is False
    error_text = "\n".join(report["errors"])
    assert "at least 4 brands/stores" in error_text
    assert "over the max 3 SKU limit" in error_text
    assert "low, mid, and high price bands" in error_text
