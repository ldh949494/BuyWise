import pytest

from app.services.intent_service import IntentService


@pytest.mark.anyio
async def test_extract_related_category_recommendation_is_not_compare_intent() -> None:
    service = IntentService()

    need = await service.extract("再为我推荐跟它比较搭配的鼠标", history_context={"category": "机械键盘"})

    assert need.intent == "商品推荐"
    assert need.category == "鼠标"
