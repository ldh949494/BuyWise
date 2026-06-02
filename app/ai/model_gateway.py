"""AI model gateway protocol."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Protocol


class AIModelGateway(Protocol):
    async def chat(self, messages: list[dict]) -> str:
        ...

    def stream_chat(self, messages: list[dict]) -> AsyncIterator[str]:
        ...

    async def generate_recommendation(self, need: Any, products: list[Any]) -> str:
        ...

    def stream_recommendation(self, need: Any, products: list[Any]) -> AsyncIterator[str]:
        ...

    async def generate_clarify_question(self, need: Any) -> str:
        ...

    def stream_clarify_question(self, need: Any) -> AsyncIterator[str]:
        ...

    async def generate_compare_summary(self, user_need: Any, products: list[Any]) -> str:
        ...
