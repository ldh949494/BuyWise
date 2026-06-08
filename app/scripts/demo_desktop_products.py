"""Extra deterministic desktop products for bundle demo flows."""

from __future__ import annotations

from decimal import Decimal
from typing import Any


DEMO_DESKTOP_PRODUCTS: list[dict[str, Any]] = [
    {
        "id": 1217,
        "name": "OfficeKeys 98 办公机械键盘",
        "category": "机械键盘",
        "brand": "KeyNova",
        "sku": "demo-keyboard-officekeys-98",
        "price": Decimal("459.00"),
        "original_price": Decimal("559.00"),
        "platform": "京东",
        "product_url": "https://www.keychron.com/products/keychron-k10-pro-qmk-via-wireless-mechanical-keyboard",
        "image_url": "https://buywise-1392410096.cos.ap-guangzhou.myqcloud.com/product-images/beta-keyboard-keychron-v1-he/V1HE-d15c5a737512df61.jpg",
        "image_urls": ["https://buywise-1392410096.cos.ap-guangzhou.myqcloud.com/product-images/beta-keyboard-keychron-v1-he/V1HE-d15c5a737512df61.jpg"],
        "rating": Decimal("4.70"),
        "sales": 980,
        "description": "98 配列无线机械键盘，兼顾数字区和桌面空间。",
        "specs": {"layout": "98键", "switch": "静音茶轴", "connection": "蓝牙/2.4G/有线"},
        "tags": ["无线", "办公", "低噪音"],
        "suitable_scene": ["办公", "写代码", "学习"],
        "stock": 22,
        "stock_status": "in_stock",
        "review_summary": "数字区保留，桌面占用比全尺寸更小。",
    },
    {
        "id": 1218,
        "name": "MeetBuds Clear 会议耳机",
        "category": "蓝牙耳机",
        "brand": "SoundAir",
        "sku": "demo-earbuds-meetbuds-clear",
        "price": Decimal("459.00"),
        "original_price": Decimal("599.00"),
        "platform": "天猫",
        "product_url": "https://www.jabra.com/business/office-headsets",
        "image_url": "https://buywise-1392410096.cos.ap-guangzhou.myqcloud.com/product-images/beta-earbuds-soundcore-liberty-4-nc/A3947Z11_4088025e-9f6e-4ec4-ad98-69d8d7dbf357-6e213c5f2636a16a.png",
        "image_urls": ["https://buywise-1392410096.cos.ap-guangzhou.myqcloud.com/product-images/beta-earbuds-soundcore-liberty-4-nc/A3947Z11_4088025e-9f6e-4ec4-ad98-69d8d7dbf357-6e213c5f2636a16a.png"],
        "rating": Decimal("4.60"),
        "sales": 880,
        "description": "通话降噪更稳的会议耳机，适合网课和远程办公。",
        "specs": {"noise_canceling": "通话降噪", "battery": "32小时", "microphone": "双麦"},
        "tags": ["通话", "无线", "办公"],
        "suitable_scene": ["办公", "学习", "通勤"],
        "stock": 36,
        "stock_status": "in_stock",
        "review_summary": "语音清晰，会议场景更可靠。",
    },
]
