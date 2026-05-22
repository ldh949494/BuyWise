import pytest

from app.schemas.chat import StructuredNeed
from app.services.intent_service import IntentService


class FakeLLMClient:
    def __init__(self, content: str | None = None, should_fail: bool = False) -> None:
        self.content = content or ""
        self.should_fail = should_fail
        self.messages = []

    async def chat(self, messages):
        self.messages.append(messages)
        if self.should_fail:
            raise RuntimeError("llm unavailable")
        return self.content


@pytest.mark.anyio
async def test_extract_recommendation_need_from_text() -> None:
    service = IntentService()

    need = await service.extract("帮我推荐一个300以内适合宿舍写代码的低噪音机械键盘，最好无线，性价比高")

    assert isinstance(need, StructuredNeed)
    assert need.intent == "商品推荐"
    assert need.category == "机械键盘"
    assert need.budget_max == 300
    assert need.scenario == "宿舍"
    assert need.preferences == ["低噪音", "无线", "性价比"]
    assert need.need_clarify is False
    assert need.missing_fields == []


@pytest.mark.anyio
async def test_extract_other_intents_and_budget_patterns() -> None:
    service = IntentService()

    compare_need = await service.extract("对比一下不超过500元的蓝牙耳机，通勤用，要降噪")
    alternative_need = await service.extract("帮我找平替台灯，预算300，学习用，要护眼")
    price_need = await service.extract("这个充电宝价格值不值，200元以内，大容量")
    params_need = await service.extract("双肩包的参数怎么选，办公通勤要轻便")

    assert compare_need.intent == "商品对比"
    assert compare_need.budget_max == 500
    assert compare_need.category == "蓝牙耳机"
    assert compare_need.preferences == ["降噪"]
    assert alternative_need.intent == "找平替"
    assert alternative_need.category == "台灯"
    assert alternative_need.preferences == ["护眼"]
    assert price_need.intent == "价格判断"
    assert price_need.category == "充电宝"
    assert price_need.preferences == ["大容量"]
    assert params_need.intent == "参数咨询"
    assert params_need.category == "双肩包"
    assert params_need.scenario == "办公"


@pytest.mark.anyio
async def test_extract_marks_underspecified_request_for_clarification() -> None:
    service = IntentService()

    need = await service.extract("推荐一个耳机")

    assert need.intent == "商品推荐"
    assert need.category == "蓝牙耳机"
    assert need.need_clarify is True
    assert need.missing_fields == ["budget_max", "scenario", "preferences"]


@pytest.mark.anyio
async def test_extract_merges_image_info_and_history_context() -> None:
    service = IntentService()

    need = await service.extract(
        "找个500以内通勤用的",
        image_info={"category": "双肩包", "features": ["轻便", "大容量"]},
        history_context={"scenario": "办公"},
    )

    assert need.intent == "商品推荐"
    assert need.category == "双肩包"
    assert need.budget_max == 500
    assert need.scenario == "通勤"
    assert need.preferences == ["轻便", "大容量"]
    assert need.need_clarify is False


@pytest.mark.anyio
async def test_extract_prefers_llm_structured_need_when_available() -> None:
    llm = FakeLLMClient(
        """
        {
          "intent": "商品推荐",
          "category": "蓝牙耳机",
          "budget_max": 800,
          "scenario": "通勤",
          "preferences": ["降噪", "轻便"],
          "avoid": ["入耳压迫"],
          "need_clarify": false,
          "missing_fields": []
        }
        """
    )
    service = IntentService(llm_client=llm)

    need = await service.extract("我想买个上班路上用的耳机，价格别太高")

    assert need.intent == "商品推荐"
    assert need.category == "蓝牙耳机"
    assert need.budget_max == 800
    assert need.scenario == "通勤"
    assert need.preferences == ["降噪", "轻便"]
    assert need.avoid == ["入耳压迫"]
    assert need.need_clarify is False
    assert llm.messages


@pytest.mark.anyio
async def test_extract_normalizes_llm_intent_and_ignores_non_core_missing_fields() -> None:
    llm = FakeLLMClient(
        """
        {
          "intent": "推荐",
          "category": "键盘",
          "budget_max": 300,
          "scenario": "宿舍写代码",
          "preferences": ["静音", "蓝牙", "性价比高"],
          "need_clarify": true,
          "missing_fields": ["轴体类型", "连接方式", "背光需求"]
        }
        """
    )
    service = IntentService(llm_client=llm)

    need = await service.extract("帮我推荐一个300以内适合宿舍写代码的低噪音无线机械键盘")

    assert need.intent == "商品推荐"
    assert need.category == "机械键盘"
    assert need.scenario == "宿舍"
    assert need.preferences == ["低噪音", "无线", "性价比"]
    assert need.need_clarify is False
    assert need.missing_fields == []


@pytest.mark.anyio
async def test_extract_normalizes_realistic_llm_recommendation_aliases() -> None:
    samples = [
        (
            """
            ```json
            {
              "intent": "推荐",
              "category": "耳麦",
              "budget_max": "300",
              "scenario": "地铁通勤",
              "preferences": ["主动降噪", "蓝牙"],
              "avoid": [],
              "need_clarify": false,
              "missing_fields": []
            }
            ```
            """,
            {
                "intent": "商品推荐",
                "category": "蓝牙耳机",
                "budget_max": 300,
                "scenario": "通勤",
                "preferences": ["降噪", "无线"],
            },
        ),
        (
            """
            {
              "intent": "找推荐",
              "category": "护眼灯",
              "budget_max": 200,
              "scenario": "宿舍床边阅读",
              "preferences": ["护眼"],
              "avoid": ["太占地方"],
              "need_clarify": false,
              "missing_fields": []
            }
            """,
            {
                "intent": "商品推荐",
                "category": "台灯",
                "budget_max": 200,
                "scenario": "宿舍",
                "preferences": ["护眼"],
            },
        ),
        (
            """
            {
              "intent": "商品推荐",
              "category": "移动电源",
              "budget_max": 150,
              "scenario": "短途旅行",
              "preferences": ["快充", "大容量"],
              "avoid": [],
              "need_clarify": false,
              "missing_fields": []
            }
            """,
            {
                "intent": "商品推荐",
                "category": "充电宝",
                "budget_max": 150,
                "scenario": "旅行",
                "preferences": ["快充", "大容量"],
            },
        ),
    ]

    for content, expected in samples:
        service = IntentService(llm_client=FakeLLMClient(content))

        need = await service.extract("demo request")

        assert need.intent == expected["intent"]
        assert need.category == expected["category"]
        assert need.budget_max == expected["budget_max"]
        assert need.scenario == expected["scenario"]
        assert need.preferences == expected["preferences"]
        assert need.need_clarify is False


@pytest.mark.anyio
async def test_extract_falls_back_to_rules_when_llm_fails() -> None:
    service = IntentService(llm_client=FakeLLMClient(should_fail=True))

    need = await service.extract("帮我推荐一个300以内适合宿舍写代码的低噪音机械键盘")

    assert need.intent == "商品推荐"
    assert need.category == "机械键盘"
    assert need.budget_max == 300
    assert need.scenario == "宿舍"
    assert need.preferences == ["低噪音"]
    assert need.need_clarify is False
