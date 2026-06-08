from __future__ import annotations

import csv
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import Product
from app.scripts.rewrite_product_images import rewrite_product_images


def make_session_factory():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def write_image_csv(path, image_url: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["sku", "image_url", "image_urls"])
        writer.writeheader()
        writer.writerow({"sku": "demo", "image_url": image_url, "image_urls": json.dumps([image_url])})


def test_rewrite_product_images_dry_run_reports_without_updating(tmp_path) -> None:
    session_factory = make_session_factory()
    with session_factory() as db:
        db.add(Product(id=1, sku="demo", name="Demo", image_url="https://old.example-real.test/main.jpg"))
        db.commit()
    image_url = "https://buywise-1392410096.cos.ap-guangzhou.myqcloud.com/product-images/demo/main.jpg"
    csv_path = tmp_path / "products.csv"
    write_image_csv(csv_path, image_url)

    summary = rewrite_product_images(source_path=csv_path, session_factory=session_factory, dry_run=True)

    with session_factory() as db:
        product = db.get(Product, 1)
        assert product.image_url == "https://old.example-real.test/main.jpg"
    assert summary.products_updated == 1
    assert summary.updates[0]["next"] == {"image_url": image_url, "image_urls": [image_url]}


def test_rewrite_product_images_apply_updates_image_fields(tmp_path) -> None:
    session_factory = make_session_factory()
    with session_factory() as db:
        db.add(Product(id=1, sku="demo", name="Demo", image_url="https://old.example-real.test/main.jpg"))
        db.commit()
    image_url = "https://buywise-1392410096.cos.ap-guangzhou.myqcloud.com/product-images/demo/main.jpg"
    csv_path = tmp_path / "products.csv"
    write_image_csv(csv_path, image_url)

    summary = rewrite_product_images(source_path=csv_path, session_factory=session_factory, dry_run=False)

    with session_factory() as db:
        product = db.get(Product, 1)
        assert product.image_url == image_url
        assert product.image_urls == [image_url]
    assert summary.products_updated == 1
