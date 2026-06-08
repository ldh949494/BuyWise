from __future__ import annotations

import csv
from email.message import Message
from io import StringIO
from pathlib import Path

from app.scripts import validate_product_images as image_validator
from app.scripts.validate_product_images import validate_product_images


FIELDNAMES = ["sku", "name", "category", "product_url", "image_url", "image_urls"]
COS_HOST = "buywise-1392410096.cos.ap-guangzhou.myqcloud.com"


def write_products_csv(path: Path, rows: list[dict[str, str]]) -> None:
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=FIELDNAMES)
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(buffer.getvalue(), encoding="utf-8")


def row(sku: str, image_url: str) -> dict[str, str]:
    return {
        "sku": sku,
        "name": f"Product {sku}",
        "category": "机械键盘",
        "product_url": f"https://shop.example-real.test/products/{sku}",
        "image_url": image_url,
        "image_urls": f'["{image_url}"]',
    }


def test_validate_product_images_rejects_placeholder_hosts(tmp_path) -> None:
    csv_path = tmp_path / "products.csv"
    write_products_csv(csv_path, [row("demo", "https://example.com/images/demo.jpg")])

    report = validate_product_images(csv_paths=[csv_path], include_seed_profiles=False)

    assert report["ok"] is False
    assert "placeholder host example.com" in report["errors"][0]


def test_validate_product_images_rejects_duplicate_image_urls(tmp_path) -> None:
    image_url = f"https://{COS_HOST}/product-images/shared/main.jpg"
    csv_path = tmp_path / "products.csv"
    write_products_csv(csv_path, [row("one", image_url), row("two", image_url)])

    report = validate_product_images(
        csv_paths=[csv_path],
        include_seed_profiles=False,
        require_unique_image_urls=True,
    )

    assert report["ok"] is False
    assert "image_url is reused by 2 products" in report["errors"][-1]


def test_validate_product_images_rejects_small_http_images(tmp_path, monkeypatch) -> None:
    image_url = f"https://{COS_HOST}/product-images/demo/main.jpg"
    csv_path = tmp_path / "products.csv"
    write_products_csv(csv_path, [row("demo", image_url)])

    monkeypatch.setattr(image_validator, "urlopen", lambda *args, **kwargs: FakeResponse(content_length="512"))

    report = validate_product_images(
        csv_paths=[csv_path],
        include_seed_profiles=False,
        check_http=True,
        min_image_bytes=10_000,
    )

    assert report["ok"] is False
    assert "image_url is too small: 512 bytes" in report["errors"][0]


def test_validate_product_images_rejects_duplicate_http_etags(tmp_path, monkeypatch) -> None:
    csv_path = tmp_path / "products.csv"
    write_products_csv(
        csv_path,
        [
            row("one", f"https://{COS_HOST}/product-images/one/main.jpg"),
            row("two", f"https://{COS_HOST}/product-images/two/main.jpg"),
        ],
    )

    monkeypatch.setattr(image_validator, "urlopen", lambda *args, **kwargs: FakeResponse(etag='"same"'))

    report = validate_product_images(
        csv_paths=[csv_path],
        include_seed_profiles=False,
        check_http=True,
        require_unique_http_etags=True,
    )

    assert report["ok"] is False
    assert "image content ETag is reused by 2 products" in report["errors"][-1]


class FakeResponse:
    def __init__(
        self,
        *,
        content_type: str = "image/jpeg",
        content_length: str = "20000",
        etag: str = '"etag"',
    ) -> None:
        self.headers = Message()
        self.headers["content-type"] = content_type
        self.headers["content-length"] = content_length
        self.headers["etag"] = etag

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None
