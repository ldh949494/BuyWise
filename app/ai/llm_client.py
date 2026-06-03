"""LLM client wrapper with mock and OpenAI-compatible providers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Protocol

from app.ai.prompts import RECOMMEND_PROMPT
from app.core.config import settings
from app.core.resilience import provider_policy, provider_stream, run_provider_call_async


UNSUPPORTED_CLAIM_KEYWORDS = [
    "优惠券",
    "券",
    "满减",
    "折扣",
    "打折",
    "促销",
    "包邮",
    "免邮",
    "保修",
    "售后",
    "官方认证",
    "正品保证",
    "闪购",
    "秒杀",
]
UNSUPPORTED_CLAIM_FALLBACK = "我只能基于当前商品卡片做推荐，暂无可验证的优惠券、促销或额外平台功能信息。"


class LLMProvider(Protocol):
    async def chat(self, messages: list[dict[str, str]], *, max_tokens: int | None = None) -> str:
        ...

    async def stream_chat(self, messages: list[dict[str, str]], *, max_tokens: int | None = None) -> AsyncIterator[str]:
        ...


class MockLLMProvider:
    async def chat(self, messages: list[dict[str, str]], *, max_tokens: int | None = None) -> str:
        user_messages = [
            message.get("content", "")
            for message in messages
            if message.get("role") == "user"
        ]
        content = user_messages[-1] if user_messages else ""
        return f"Mock shopping guidance for: {content}"

    async def stream_chat(self, messages: list[dict[str, str]], *, max_tokens: int | None = None) -> AsyncIterator[str]:
        content = await self.chat(messages, max_tokens=max_tokens)
        chunk_size = 8
        for index in range(0, len(content), chunk_size):
            yield content[index : index + chunk_size]


class OpenAICompatibleProvider:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        client: Any | None = None,
    ) -> None:
        self.model = model or settings.llm_model
        self.client = client or self._create_client(base_url=base_url, api_key=api_key)

    async def chat(self, messages: list[dict[str, str]], *, max_tokens: int | None = None) -> str:
        kwargs = self._completion_kwargs(messages, max_tokens=max_tokens)
        response = await self.client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        return content or ""

    async def stream_chat(self, messages: list[dict[str, str]], *, max_tokens: int | None = None) -> AsyncIterator[str]:
        kwargs = self._completion_kwargs(messages, max_tokens=max_tokens)
        stream = await self.client.chat.completions.create(**kwargs, stream=True)
        async for chunk in stream:
            if not chunk.choices:
                continue
            content = chunk.choices[0].delta.content
            if content:
                yield content

    def _completion_kwargs(self, messages: list[dict[str, str]], *, max_tokens: int | None = None) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        return kwargs

    def _create_client(self, *, base_url: str | None, api_key: str | None) -> Any:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:  # pragma: no cover - dependency is in requirements.
            raise RuntimeError("openai package is required for OpenAI-compatible LLM provider") from exc

        resolved_api_key = api_key if api_key is not None else settings.llm_api_key
        if not resolved_api_key:
            raise RuntimeError("LLM_API_KEY is required for OpenAI-compatible LLM provider")
        return AsyncOpenAI(
            base_url=base_url or settings.llm_base_url,
            api_key=resolved_api_key,
            timeout=provider_policy("llm", "chat").timeout_seconds,
        )


class LLMClient:
    def __init__(
        self,
        provider: LLMProvider | None = None,
        provider_name: str | None = None,
    ) -> None:
        self.provider = provider or self._build_provider(provider_name or settings.llm_provider)

    async def chat(self, messages: list[dict], *, max_tokens: int | None = None) -> str:
        normalized = [
            {"role": str(message.get("role", "user")), "content": str(message.get("content", ""))}
            for message in messages
        ]
        policy = provider_policy("llm", "chat")
        return await run_provider_call_async(
            policy,
            lambda: self._provider_chat(normalized, max_tokens=max_tokens),
            capacity_resource="llm",
        )

    async def stream_chat(self, messages: list[dict], *, max_tokens: int | None = None) -> AsyncIterator[str]:
        normalized = [
            {"role": str(message.get("role", "user")), "content": str(message.get("content", ""))}
            for message in messages
        ]
        async with provider_stream(provider_policy("llm", "stream_chat"), capacity_resource="llm"):
            async for chunk in self._provider_stream_chat(normalized, max_tokens=max_tokens):
                yield chunk

    async def _provider_chat(self, messages: list[dict[str, str]], *, max_tokens: int | None = None) -> str:
        if max_tokens is None:
            return await self.provider.chat(messages)
        try:
            return await self.provider.chat(messages, max_tokens=max_tokens)
        except TypeError:
            return await self.provider.chat(messages)

    async def _provider_stream_chat(
        self,
        messages: list[dict[str, str]],
        *,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        if max_tokens is None:
            async for chunk in self.provider.stream_chat(messages):
                yield chunk
            return
        try:
            stream = self.provider.stream_chat(messages, max_tokens=max_tokens)
        except TypeError:
            stream = self.provider.stream_chat(messages)
        async for chunk in stream:
            yield chunk

    async def generate_recommendation(self, need: Any, products: list[Any], *, concise: bool = False, max_tokens: int | None = None) -> str:
        if not products:
            return "暂时没有找到完全匹配的商品，可以放宽预算或调整条件。"
        reply = await self.chat(self.recommendation_messages(need, products, concise=concise), max_tokens=max_tokens)
        return self._guard_recommendation_reply(reply, products)

    async def stream_recommendation(
        self,
        need: Any,
        products: list[Any],
        *,
        concise: bool = False,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        if not products:
            yield "暂时没有找到完全匹配的商品，可以放宽预算或调整条件。"
            return
        async for chunk in self.stream_chat(
            self.recommendation_messages(need, products, concise=concise),
            max_tokens=max_tokens,
        ):
            yield chunk

    def recommendation_messages(self, need: Any, products: list[Any], *, concise: bool = False) -> list[dict[str, str]]:
        system_prompt = RECOMMEND_PROMPT.strip()
        if concise:
            system_prompt = (
                system_prompt
                + "\nKeep the reply short: at most 3 concise bullet points. "
                "Focus only on the top pick, why it fits, and one pre-purchase caution. "
                "Do not repeat full price or rating lists already shown in product cards."
            )
        return [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": self._recommendation_prompt(need, products),
            },
        ]

    async def generate_clarify_question(self, need: Any) -> str:
        missing_fields = self._coerce_list(self._get_value(need, "missing_fields"))
        if not missing_fields:
            return "请补充预算、使用场景或偏好，我会继续帮你筛选。"

        labels = {
            "category": "商品品类",
            "budget_max": "预算上限",
            "scenario": "使用场景",
            "preferences": "偏好",
        }
        missing = "、".join(labels.get(field, field) for field in missing_fields)
        return f"为了更准确推荐，请补充：{missing}。"

    async def stream_clarify_question(self, need: Any) -> AsyncIterator[str]:
        question = await self.generate_clarify_question(need)
        chunk_size = 8
        for index in range(0, len(question), chunk_size):
            yield question[index : index + chunk_size]

    async def generate_compare_summary(self, user_need: Any, products: list[Any]) -> str:
        if not products:
            return "暂时没有可对比的商品。"
        return await self.chat(
            [
                {
                    "role": "system",
                    "content": "You are BuyWise. Summarize the comparison in concise Chinese.",
                },
                {
                    "role": "user",
                    "content": self._compare_prompt(user_need, products),
                },
            ]
        )

    def generate_reply(self, user_query: str) -> str:
        return f"Mock shopping guidance for: {user_query}"

    def _build_provider(self, provider_name: str) -> LLMProvider:
        normalized = provider_name.strip().lower()
        if normalized == "mock":
            return MockLLMProvider()
        if normalized in {"openai", "openai-compatible"}:
            return OpenAICompatibleProvider()
        raise ValueError("LLM_PROVIDER must be 'mock', 'openai', or 'openai-compatible'.")

    def _recommendation_prompt(self, need: Any, products: list[Any]) -> str:
        lines = [
            "Need:",
            self._format_mapping(need),
            "Products:",
        ]
        for product in products:
            lines.append(self._format_mapping(product))
        return "\n".join(lines)

    def _compare_prompt(self, user_need: Any, products: list[Any]) -> str:
        lines = [f"User need: {user_need}", "Products:"]
        for product in products:
            lines.append(self._format_mapping(product))
        return "\n".join(lines)

    def _format_mapping(self, source: Any) -> str:
        keys = [
            "id",
            "name",
            "category",
            "price",
            "rating",
            "score",
            "reason",
            "budget_match",
            "scenario_match",
            "conflicts",
            "alternatives",
        ]
        parts = []
        for key in keys:
            value = self._get_value(source, key)
            if value not in (None, [], ""):
                parts.append(f"{key}={value}")
        return "; ".join(parts)

    def _get_value(self, source: Any, key: str) -> Any:
        if isinstance(source, dict):
            return source.get(key)
        return getattr(source, key, None)

    def _guard_recommendation_reply(self, reply: str, products: list[Any]) -> str:
        if not reply:
            return self._template_recommendation_reply(products)
        if self._has_unsupported_claim(reply, products):
            return self._template_recommendation_reply(products)
        return reply

    def _has_unsupported_claim(self, reply: str, products: list[Any]) -> bool:
        for keyword in UNSUPPORTED_CLAIM_KEYWORDS:
            if keyword not in reply:
                continue
            if not self._claim_supported(keyword, products):
                return True
        return False

    def _claim_supported(self, keyword: str, products: list[Any]) -> bool:
        return any(keyword in self._format_mapping(product) for product in products)

    def _template_recommendation_reply(self, products: list[Any]) -> str:
        product_lines = []
        for product in products[:3]:
            name = self._get_value(product, "name")
            reason = self._get_value(product, "reason")
            if not name:
                continue
            if reason:
                product_lines.append(f"{name}：{reason}")
            else:
                product_lines.append(str(name))
        if not product_lines:
            return "暂时没有找到完全匹配的商品，可以放宽预算或调整条件。"
        return "基于当前商品卡片，建议优先看：" + "；".join(product_lines) + "。" + UNSUPPORTED_CLAIM_FALLBACK

    def _coerce_list(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value if item]
        return [str(value)]
