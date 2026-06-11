"""Seed deterministic product data for Android contract flows."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.scripts.demo_broad_products import DEMO_BROAD_PRODUCTS
from app.models.product import Product
from app.scripts.demo_desktop_products import DEMO_DESKTOP_PRODUCTS
from app.scripts.demo_products import DEMO_SHOWCASE_PRODUCTS

ANDROID_CONTRACT_PRODUCTS: list[dict[str, Any]] = [
    {
        "id": 1001,
        "name": "K87 静音红轴机械键盘",
        "category": "机械键盘",
        "brand": "KeyNova",
        "sku": "android-keyboard-k87",
        "price": Decimal("269.00"),
        "original_price": Decimal("329.00"),
        "platform": "京东",
        "product_url": "https://www.keychron.com/products/keychron-k3-max-se-qmk-wireless-custom-mechanical-keyboard",
        "image_url": "https://buywise-1392410096.cos.ap-guangzhou.myqcloud.com/product-images/beta-keyboard-keychron-k3-max-se/Keychron-K3-Max-SE-features-451e731bc6f18fcc.jpg",
        "image_urls": ["https://buywise-1392410096.cos.ap-guangzhou.myqcloud.com/product-images/beta-keyboard-keychron-k3-max-se/Keychron-K3-Max-SE-features-451e731bc6f18fcc.jpg"],
        "rating": Decimal("4.80"),
        "sales": 1800,
        "description": "适合宿舍写代码的低噪音 87 键机械键盘。",
        "specs": {"layout": "87键", "switch": "静音红轴", "connection": "有线"},
        "tags": ["静音", "低噪音", "编程", "性价比"],
        "suitable_scene": ["宿舍", "写代码", "学习"],
        "stock": 25,
        "stock_status": "in_stock",
        "review_summary": "按键安静，适合宿舍和夜间输入。",
    },
    {
        "id": 1002,
        "name": "Lite68 办公静音键盘",
        "category": "机械键盘",
        "brand": "KeyNova",
        "sku": "android-keyboard-lite68",
        "price": Decimal("329.00"),
        "original_price": Decimal("399.00"),
        "platform": "天猫",
        "product_url": "https://www.keychron.com/products/keychron-v1-he-magnetic-switch-keyboard",
        "image_url": "https://buywise-1392410096.cos.ap-guangzhou.myqcloud.com/product-images/beta-keyboard-keychron-v1-he/V1HE-d15c5a737512df61.jpg",
        "image_urls": ["https://buywise-1392410096.cos.ap-guangzhou.myqcloud.com/product-images/beta-keyboard-keychron-v1-he/V1HE-d15c5a737512df61.jpg"],
        "rating": Decimal("4.50"),
        "sales": 900,
        "description": "紧凑 68 键配列，支持无线连接，适合通勤办公。",
        "specs": {"layout": "68键", "switch": "静音茶轴", "connection": "蓝牙/有线"},
        "tags": ["静音", "无线", "办公"],
        "suitable_scene": ["办公", "通勤", "写代码"],
        "stock": 18,
        "stock_status": "in_stock",
        "review_summary": "连接方式灵活，桌面占用小。",
    },
    {
        "id": 1003,
        "name": "AirBuds Pro 主动降噪耳机",
        "category": "蓝牙耳机",
        "brand": "SoundAir",
        "sku": "android-earbuds-pro",
        "price": Decimal("399.00"),
        "original_price": Decimal("499.00"),
        "platform": "京东",
        "product_url": "https://electronics.sony.com/audio/headphones/truly-wireless-earbuds/p/wf1000xm6-b",
        "image_url": "https://buywise-1392410096.cos.ap-guangzhou.myqcloud.com/product-images/beta-earbuds-sony-wf1000xm6/WF-1000XM6-357ed4a671f4579e.jpg",
        "image_urls": ["https://buywise-1392410096.cos.ap-guangzhou.myqcloud.com/product-images/beta-earbuds-sony-wf1000xm6/WF-1000XM6-357ed4a671f4579e.jpg"],
        "rating": Decimal("4.70"),
        "sales": 2100,
        "description": "主动降噪和通透模式兼备，适合地铁通勤。",
        "specs": {"noise_canceling": "ANC主动降噪", "battery": "30小时", "bluetooth": "5.3"},
        "tags": ["主动降噪", "通勤", "无线"],
        "suitable_scene": ["通勤", "办公", "学习"],
        "stock": 40,
        "stock_status": "in_stock",
        "review_summary": "降噪稳定，通话清晰。",
    },
    {
        "id": 1004,
        "name": "StudyLamp Pro 护眼台灯",
        "category": "台灯",
        "brand": "LightWise",
        "sku": "android-lamp-study-pro",
        "price": Decimal("299.00"),
        "original_price": Decimal("369.00"),
        "platform": "天猫",
        "product_url": "https://www.ikea.com/us/en/p/tertial-work-lamp-dark-gray-20355434/",
        "image_url": "https://buywise-1392410096.cos.ap-guangzhou.myqcloud.com/product-images/beta-lamp-ikea-tertial-gray/tertial-work-lamp-dark-gray__0609306_pe684440_s5-2a6b8a3b20fd0ad4.webp",
        "image_urls": ["https://buywise-1392410096.cos.ap-guangzhou.myqcloud.com/product-images/beta-lamp-ikea-tertial-gray/tertial-work-lamp-dark-gray__0609306_pe684440_s5-2a6b8a3b20fd0ad4.webp"],
        "rating": Decimal("4.80"),
        "sales": 1600,
        "description": "AA 级照度护眼台灯，适合长时间阅读和备考。",
        "specs": {"brightness": "1200lx", "color_temp": "3000K-5000K", "dimming": "无级调光"},
        "tags": ["护眼", "阅读", "无级调光"],
        "suitable_scene": ["学习", "阅读", "宿舍"],
        "stock": 32,
        "stock_status": "in_stock",
        "review_summary": "照度均匀，长时间阅读更舒适。",
    },
    {
        "id": 1005,
        "name": "PowerMax 20000mAh 充电宝",
        "category": "充电宝",
        "brand": "PowerMax",
        "sku": "android-powerbank-20000",
        "price": Decimal("159.00"),
        "original_price": Decimal("199.00"),
        "platform": "京东",
        "product_url": "https://www.anker.com/products/a110a-anker-prime-26k-300w-power-bank",
        "image_url": "https://buywise-1392410096.cos.ap-guangzhou.myqcloud.com/product-images/beta-powerbank-anker-prime-26k-300w/A110AH11_Richimage_TD01_US_V1_41ed3782-6e72-4335-8e1b-41b2fa7b7d35_3838x-404e23021470d369.png",
        "image_urls": ["https://buywise-1392410096.cos.ap-guangzhou.myqcloud.com/product-images/beta-powerbank-anker-prime-26k-300w/A110AH11_Richimage_TD01_US_V1_41ed3782-6e72-4335-8e1b-41b2fa7b7d35_3838x-404e23021470d369.png"],
        "rating": Decimal("4.60"),
        "sales": 3200,
        "description": "大容量快充移动电源，适合旅行和重度手机用户。",
        "specs": {"capacity": "20000mAh", "output": "22.5W", "ports": "USB-A*2 + USB-C"},
        "tags": ["大容量", "快充", "旅行"],
        "suitable_scene": ["旅行", "通勤", "应急"],
        "stock": 60,
        "stock_status": "in_stock",
        "review_summary": "容量充足，适合短途旅行。",
    },
]
DEMO_PROFILE_PRODUCTS: list[dict[str, Any]] = [
    *ANDROID_CONTRACT_PRODUCTS,
    *DEMO_SHOWCASE_PRODUCTS,
    *DEMO_DESKTOP_PRODUCTS,
    *DEMO_BROAD_PRODUCTS,
]


def seed_android_contract_products(db: Session) -> list[Product]:
    """Insert or update deterministic products used by Android API contract tests."""

    return upsert_products(db, ANDROID_CONTRACT_PRODUCTS)


def seed_demo_products(db: Session) -> list[Product]:
    """Insert or update products curated for live demo conversations."""

    return upsert_products(db, DEMO_PROFILE_PRODUCTS)


def upsert_products(db: Session, products_data: list[dict[str, Any]]) -> list[Product]:
    seeded_products: list[Product] = []
    for product_data in products_data:
        product = db.get(Product, product_data["id"])
        if product is None:
            product = Product(**product_data)
            db.add(product)
        else:
            for key, value in product_data.items():
                setattr(product, key, value)
        seeded_products.append(product)

    db.commit()
    for product in seeded_products:
        db.refresh(product)
    return seeded_products


def seed_products(
    session_factory: Callable[[], Session] = SessionLocal,
    profile: str = "android-contract",
) -> dict[str, int]:
    with session_factory() as db:
        existing_ids = set(db.scalars(select(Product.id)).all())
        products = _seed_profile(db, profile)
        inserted = sum(1 for product in products if product.id not in existing_ids)
        return {"inserted": inserted, "updated": len(products) - inserted}


def _seed_profile(db: Session, profile: str) -> list[Product]:
    if profile == "android-contract":
        return seed_android_contract_products(db)
    if profile == "demo":
        return seed_demo_products(db)
    raise ValueError("profile must be 'android-contract' or 'demo'.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed deterministic BuyWise product data.")
    parser.add_argument(
        "--profile",
        choices=["android-contract", "demo"],
        default="android-contract",
        help="Seed profile to apply. Use demo for live demonstration data.",
    )
    args = parser.parse_args()

    result = seed_products(profile=args.profile)
    print(f"Inserted {result['inserted']} products, updated {result['updated']} products.")


if __name__ == "__main__":
    main()
