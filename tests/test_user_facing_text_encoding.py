from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
USER_VISIBLE_FILES = [
    ROOT / "app" / "ai" / "llm_client.py",
    ROOT / "app" / "ai" / "prompts.py",
    ROOT / "app" / "scripts" / "seed_products.py",
    ROOT / "app" / "services" / "chat_service.py",
    ROOT / "app" / "utils" / "text_builder.py",
    ROOT / "data" / "products.csv",
    ROOT / "data" / "rag_eval" / "shopping_needs.jsonl",
]
MOJIBAKE_MARKERS = (
    "闈",
    "鏈",
    "鍟",
    "浣",
    "瀹",
    "鐨",
    "锛",
    "銆",
    "\u93b6",
    "\u6daf",
    "\u935f",
    "\u95c8",
    "\u7029",
    "\u951b",
    "\u9286",
    "\ufffd",
)


def test_user_visible_chinese_text_is_utf8() -> None:
    for path in USER_VISIBLE_FILES:
        text = path.read_text(encoding="utf-8")
        assert not any(marker in text for marker in MOJIBAKE_MARKERS), path


def test_llm_fallbacks_keep_expected_chinese_copy() -> None:
    text = (ROOT / "app" / "ai" / "llm_client.py").read_text(encoding="utf-8")

    assert "没有找到匹配商品" in text
    assert "为了更准确推荐，请补充" in text
    assert "暂时没有可对比的商品" in text


def test_backend_seed_data_keeps_expected_chinese_copy() -> None:
    text = (ROOT / "app" / "scripts" / "seed_products.py").read_text(encoding="utf-8")
    csv_text = (ROOT / "data" / "products.csv").read_text(encoding="utf-8")

    for expected in [
        "K87 静音红轴机械键盘",
        "机械键盘",
        "蓝牙耳机",
        "护眼台灯",
        "充电宝",
        "双肩包",
    ]:
        assert expected in text or expected in csv_text
