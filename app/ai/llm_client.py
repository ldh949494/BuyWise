"""LLM client wrapper with mock and OpenAI-compatible providers."""

from __future__ import annotations

from typing import Any, Protocol

from app.core.config import settings


class LLMProvider(Protocol):
    async def chat(self, messages: list[dict[str, str]]) -> str:
        ...


class MockLLMProvider:
    async def chat(self, messages: list[dict[str, str]]) -> str:
        user_messages = [
            message.get("content", "")
            for message in messages
            if message.get("role") == "user"
        ]
        content = user_messages[-1] if user_messages else ""
        return f"Mock shopping guidance for: {content}"


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

    async def chat(self, messages: list[dict[str, str]]) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
        )
        content = response.choices[0].message.content
        return content or ""

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
        )


class LLMClient:
    def __init__(
        self,
        provider: LLMProvider | None = None,
        provider_name: str | None = None,
    ) -> None:
        self.provider = provider or self._build_provider(provider_name or settings.llm_provider)

    async def chat(self, messages: list[dict]) -> str:
        normalized = [
            {"role": str(message.get("role", "user")), "content": str(message.get("content", ""))}
            for message in messages
        ]
        return await self.provider.chat(normalized)

    async def generate_recommendation(self, need: Any, products: list[Any]) -> str:
        if not products:
            return "暂时没有找到完全匹配的商品，可以放宽预算或调整条件"
        return await self.chat(
            [
                {
                    "role": "system",
                    "content": (
                        "You are BuyWise, a shopping guide. Write a concise Chinese "
                        "recommendation based only on the provided products."
                    ),
                },
                {
                    "role": "user",
                    "content": self._recommendation_prompt(need, products),
                },
            ]
        )

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
        lines = ["Need:", self._format_mapping(need), "Products:"]
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

    def _coerce_list(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value if item]
        return [str(value)]
