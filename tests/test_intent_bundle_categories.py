import pytest

from app.services.intent_service import IntentService


class FakeLLMClient:
    def __init__(self, content: str) -> None:
        self.content = content

    async def chat(self, messages):
        return self.content


@pytest.mark.anyio
async def test_extract_normalizes_bundle_categories_from_llm_and_rules() -> None:
    service = IntentService(
        llm_client=FakeLLMClient(
            """
            {
              "intent": "bundle_recommend",
              "category": "computer peripherals",
              "must_have_categories": ["headphones", "keyboard", "mouse"],
              "preferences": ["cost-effective"],
              "need_clarify": false,
              "missing_fields": []
            }
            """
        )
    )

    need = await service.extract("给我推荐耳机，键盘，鼠标三件套，预算不多，要求性价比")

    assert need.intent == "bundle_recommend"
    assert set(need.must_have_categories) == {"机械键盘", "蓝牙耳机", "鼠标"}
    assert len(need.must_have_categories) == 3
