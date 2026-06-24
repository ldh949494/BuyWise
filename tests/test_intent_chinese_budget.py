import pytest

from app.services.intent_service import IntentService


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("message", "expected_budget"),
    [
        ("预算改到五百元", 500),
        ("如果提高预算到五百元，请帮我重新生成推荐", 500),
        ("两百以内的鼠标", 200),
        ("一千五预算的显示器", 1500),
    ],
)
async def test_extract_chinese_numeral_budget(message: str, expected_budget: int) -> None:
    service = IntentService()

    need = await service.extract(message)

    assert need.budget_max == expected_budget
