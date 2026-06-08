import csv
import json
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models import Product
from app.scripts.import_products import import_products, validate_product_rows


EXPECTED_FIELDS = {
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
}

COS_HOST = "buywise-1392410096.cos.ap-guangzhou.myqcloud.com"


def make_session_factory():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def test_products_csv_contains_50_demo_products() -> None:
    with open("data/products.csv", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 50
    assert set(rows[0]) == EXPECTED_FIELDS
    assert {row["category"] for row in rows} == {
        "机械键盘",
        "蓝牙耳机",
        "台灯",
        "充电宝",
        "双肩包",
    }
    assert len({row["name"] for row in rows}) == 50
    assert len({row["sku"] for row in rows}) == 50
    assert len({row["image_url"] for row in rows}) == 50

    for row in rows:
        assert row["sku"]
        assert "example.com" not in row["product_url"]
        assert row["image_url"].startswith(f"https://{COS_HOST}/product-images/")
        assert row["image_url"] in json.loads(row["image_urls"])
        assert Decimal(row["price"]) > 0
        assert Decimal(row["original_price"]) >= Decimal(row["price"])
        assert 0 <= float(row["rating"]) <= 5
        assert int(row["sales"]) >= 0
        assert int(row["stock"]) >= 0
        assert isinstance(json.loads(row["specs"]), dict)
        assert isinstance(json.loads(row["tags"]), list)
        assert isinstance(json.loads(row["suitable_scene"]), list)


def test_import_products_upserts_rows_by_sku() -> None:
    session_factory = make_session_factory()
    csv_path = "data/products.csv"

    first_result = import_products(csv_path, session_factory=session_factory, index_updater=None)
    second_result = import_products(csv_path, session_factory=session_factory, index_updater=None)

    with session_factory() as db:
        products = db.query(Product).order_by(Product.id).all()

    assert first_result == {"inserted": 50, "updated": 0, "failed": 0}
    assert second_result == {"inserted": 0, "updated": 50, "failed": 0}
    assert len(products) == 50
    assert products[0].sku == "beta-keyboard-keychron-k3-max-se"
    assert products[0].image_url.startswith("https://")
    assert products[0].name
    assert isinstance(products[0].specs, dict)
    assert isinstance(products[0].tags, list)
    assert isinstance(products[0].suitable_scene, list)


def test_import_products_fails_entire_batch_for_missing_required_field(tmp_path) -> None:
    csv_path = tmp_path / "bad_products.csv"
    csv_path.write_text(
        "\n".join(
            [
                "sku,name,category,price,tags",
                'SKU-1,Keyboard,机械键盘,299,"[""静音""]"',
                'SKU-2,,机械键盘,199,"[""无线""]"',
            ]
        ),
        encoding="utf-8",
    )
    session_factory = make_session_factory()

    with pytest.raises(ValueError):
        import_products(csv_path, session_factory=session_factory, index_updater=None)

    with session_factory() as db:
        assert db.query(Product).count() == 0


def test_real_catalog_validation_requires_real_urls_and_stock() -> None:
    rows = [
        {
            "sku": "REAL-1",
            "name": "Real Keyboard",
            "category": "机械键盘",
            "price": "299",
            "tags": '["静音"]',
            "product_url": "https://shop.example-real.test/products/real-keyboard",
            "image_url": "https://cdn.example-real.test/images/real-keyboard.jpg",
            "stock": "5",
        }
    ]

    validate_product_rows(rows, require_real_assets=True)


def test_real_catalog_validation_rejects_placeholder_urls() -> None:
    rows = [
        {
            "sku": "REAL-1",
            "name": "Placeholder Keyboard",
            "category": "机械键盘",
            "price": "299",
            "tags": '["静音"]',
            "product_url": "https://example.com/products/keyboard",
            "image_url": "https://cdn.example-real.test/images/keyboard.jpg",
            "stock": "5",
        }
    ]

    with pytest.raises(ValueError, match="product_url"):
        validate_product_rows(rows, require_real_assets=True)
