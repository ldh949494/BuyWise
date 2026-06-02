from decimal import Decimal
from types import SimpleNamespace

from app.schemas.chat import StructuredNeed
from app.utils.text_builder import build_product_chunks, build_product_text, build_query_from_need


def test_build_product_text_formats_product_fields_for_embedding() -> None:
    product = SimpleNamespace(
        name="K87 静音红轴机械键盘",
        category="机械键盘",
        brand="KeyNova",
        price=Decimal("329.00"),
        product_url="https://example.com/products/k87",
        image_url="https://example.com/images/k87.jpg",
        image_urls=["https://example.com/images/k87-a.jpg"],
        rating=Decimal("4.80"),
        sales=2380,
        description="适合宿舍、写代码、低噪音",
        specs={"轴体": "静音红轴", "连接": "有线"},
        tags=["静音", "红轴", "编程"],
        suitable_scene=["宿舍", "写代码"],
    )

    text = build_product_text(product)

    assert "商品名称：K87 静音红轴机械键盘" in text
    assert "类别：机械键盘" in text
    assert "品牌：KeyNova" in text
    assert "价格：329.00" in text
    assert "评分：4.80" in text
    assert "销量：2380" in text
    assert "商品描述：适合宿舍、写代码、低噪音" in text
    assert "商品参数：轴体：静音红轴；连接：有线" in text
    assert "商品标签：静音、红轴、编程" in text
    assert "适合场景：宿舍、写代码" in text
    assert "平台链接：" not in text
    assert "商品主图：" not in text
    assert "商品图片：" not in text
    assert "https://example.com" not in text


def test_build_product_chunks_splits_retrieval_fields_by_source() -> None:
    product = SimpleNamespace(
        name="K87 静音红轴机械键盘",
        category="机械键盘",
        brand="KeyNova",
        sku="beta-keyboard-k87",
        platform="京东",
        description="静音轴体和三模连接，适合宿舍写代码。",
        specs={"轴体": "静音红轴", "材质": "PBT键帽"},
        tags=["静音", "三模"],
        suitable_scene=["宿舍", "写代码"],
        review_summary="按键声音低，蓝牙稳定。",
    )

    chunks = build_product_chunks(product)
    chunks_by_type = {chunk["chunk_type"]: chunk for chunk in chunks}

    assert set(chunks_by_type) == {"product_core", "specs", "marketing_copy", "review_summary"}
    assert chunks_by_type["product_core"]["field_path"] == "core"
    assert "商品名称：K87 静音红轴机械键盘" in chunks_by_type["product_core"]["text"]
    assert "商品参数：轴体：静音红轴；材质：PBT键帽" in chunks_by_type["specs"]["text"]
    assert "商品描述：静音轴体和三模连接" in chunks_by_type["marketing_copy"]["text"]
    assert "评论摘要：按键声音低" in chunks_by_type["review_summary"]["text"]


def test_build_product_text_handles_str_list_dict_and_none_values() -> None:
    product = SimpleNamespace(
        name="AirBuds Lite",
        category=None,
        brand="SoundAir",
        price=None,
        rating=None,
        sales=None,
        description=None,
        specs=["蓝牙5.3", "通话降噪"],
        tags="通勤, 网课",
        suitable_scene=None,
    )

    text = build_product_text(product)

    assert "商品名称：AirBuds Lite" in text
    assert "品牌：SoundAir" in text
    assert "商品参数：蓝牙5.3、通话降噪" in text
    assert "商品标签：通勤, 网课" in text
    assert "类别：" not in text
    assert "适合场景：" not in text


def test_build_query_from_structured_need() -> None:
    need = StructuredNeed(
        intent="recommend",
        category="机械键盘",
        budget_max=400,
        scenario="宿舍写代码",
        preferences=["静音", "红轴"],
        avoid=["灯效太亮"],
    )

    query = build_query_from_need(need)

    assert query == "意图：recommend 类别：机械键盘 预算上限：400 场景：宿舍写代码 偏好：静音、红轴 避免：灯效太亮"


def test_build_query_from_dict_need_skips_empty_values() -> None:
    query = build_query_from_need(
        {
            "intent": "compare",
            "category": "蓝牙耳机",
            "budget_max": None,
            "scenario": "",
            "preferences": ["降噪"],
            "avoid": [],
        }
    )

    assert query == "意图：compare 类别：蓝牙耳机 偏好：降噪"
