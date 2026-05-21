from types import SimpleNamespace

import pytest

from app.ai.llm_client import LLMClient
from app.ai.prompts import (
    CLARIFY_PROMPT,
    COMPARE_PROMPT,
    INTENT_EXTRACT_PROMPT,
    RECOMMEND_PROMPT,
)
from app.schemas.chat import ProductCard, StructuredNeed


def test_prompt_constants_are_defined_for_future_llm_calls() -> None:
    assert "结构化购物需求" in INTENT_EXTRACT_PROMPT
    assert "电商导购助手" in RECOMMEND_PROMPT
    assert "追问" in CLARIFY_PROMPT
    assert "对比总结" in COMPARE_PROMPT


@pytest.mark.anyio
async def test_chat_returns_last_user_message_mock_reply() -> None:
    client = LLMClient(provider_name="mock")

    reply = await client.chat(
        [
            {"role": "system", "content": "你是导购助手"},
            {"role": "user", "content": "推荐一个键盘"},
        ]
    )

    assert reply == "Mock shopping guidance for: 推荐一个键盘"


@pytest.mark.anyio
async def test_mock_chat_stream_returns_chunks() -> None:
    client = LLMClient(provider_name="mock")

    chunks = [
        chunk
        async for chunk in client.stream_chat(
            [{"role": "user", "content": "推荐一个键盘"}]
        )
    ]

    assert chunks
    assert "".join(chunks) == "Mock shopping guidance for: 推荐一个键盘"


@pytest.mark.anyio
async def test_generate_recommendation_uses_only_given_products() -> None:
    client = LLMClient(provider_name="mock")
    need = StructuredNeed(
        intent="商品推荐",
        category="机械键盘",
        budget_max=300,
        scenario="宿舍",
        preferences=["低噪音"],
    )
    products = [
        ProductCard(
            id=1,
            name="K87 静音红轴机械键盘",
            price=299,
            rating=4.8,
            score=94,
            reason="价格符合预算；适合宿舍场景；符合低噪音偏好",
        ),
        ProductCard(
            id=2,
            name="Lite68 办公静音键盘",
            price=269,
            rating=4.6,
            score=88,
            reason="价格符合预算；符合低噪音偏好",
        ),
    ]

    reply = await client.generate_recommendation(need, products)

    assert "K87 静音红轴机械键盘" in reply
    assert "Lite68 办公静音键盘" in reply
    assert "机械键盘" in reply
    assert "不存在的商品" not in reply
    assert "价格符合预算" in reply


@pytest.mark.anyio
async def test_generate_recommendation_handles_empty_products() -> None:
    client = LLMClient(provider_name="mock")

    reply = await client.generate_recommendation({"category": "台灯"}, [])

    assert reply == "暂时没有找到完全匹配的商品，可以放宽预算或调整条件。"


@pytest.mark.anyio
async def test_generate_clarify_question_from_missing_fields() -> None:
    client = LLMClient(provider_name="mock")
    need = StructuredNeed(
        intent="商品推荐",
        category="蓝牙耳机",
        need_clarify=True,
        missing_fields=["budget_max", "scenario", "preferences"],
    )

    reply = await client.generate_clarify_question(need)

    assert "预算" in reply
    assert "使用场景" in reply
    assert "偏好" in reply


@pytest.mark.anyio
async def test_generate_compare_summary_uses_given_products() -> None:
    client = LLMClient(provider_name="mock")
    products = [
        SimpleNamespace(name="AirBuds Lite", price=199, rating=4.6, reason="通勤轻便"),
        SimpleNamespace(name="AirBuds Pro", price=399, rating=4.8, reason="降噪更强"),
    ]

    reply = await client.generate_compare_summary({"scenario": "通勤"}, products)

    assert "AirBuds Lite" in reply
    assert "AirBuds Pro" in reply
    assert "通勤轻便" in reply
    assert "降噪更强" in reply
