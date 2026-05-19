from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
USER_VISIBLE_FILES = [
    ROOT / "app" / "ai" / "llm_client.py",
    ROOT / "app" / "ai" / "prompts.py",
    ROOT / "app" / "services" / "chat_service.py",
    ROOT / "app" / "utils" / "text_builder.py",
]
MOJIBAKE_MARKERS = (
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

    assert "暂时没有找到完全匹配的商品" in text
    assert "为了更准确推荐，请补充" in text
    assert "暂时没有可对比的商品" in text
