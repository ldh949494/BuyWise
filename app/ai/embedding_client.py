"""Embedding client wrapper with mock and OpenAI-compatible providers."""

from __future__ import annotations

import hashlib
import math
import random
from typing import Any, List, Protocol

from app.core.config import settings
from app.core.resilience import provider_policy, run_provider_call


class EmbeddingProvider(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...


class MockEmbeddingProvider:
    """Mock embedding client with stable fixed-dimension vectors."""

    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension

    def embed_text(self, text: str) -> list[float]:
        seed = int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")
        generator = random.Random(seed)
        vector = [generator.uniform(-1.0, 1.0) for _ in range(self.dimension)]
        return self._normalize(vector)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]

    def _normalize(self, vector: list[float]) -> list[float]:
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


class OpenAICompatibleEmbeddingProvider:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        client: Any | None = None,
    ) -> None:
        self.model = model or settings.embedding_model
        self.client = client or self._create_client(base_url=base_url, api_key=api_key)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self.client.embeddings.create(model=self.model, input=texts)
        return [list(item.embedding) for item in response.data]

    def _create_client(self, *, base_url: str | None, api_key: str | None) -> Any:
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - dependency is in requirements.
            raise RuntimeError("openai package is required for OpenAI-compatible embedding provider") from exc

        resolved_api_key = api_key if api_key is not None else settings.effective_embedding_api_key
        if not resolved_api_key:
            raise RuntimeError("EMBEDDING_API_KEY or LLM_API_KEY is required for OpenAI-compatible embedding provider")
        return OpenAI(
            base_url=base_url or settings.effective_embedding_base_url,
            api_key=resolved_api_key,
            timeout=provider_policy("embedding", "embed_texts").timeout_seconds,
        )


class EmbeddingClient:
    def __init__(
        self,
        dimension: int = 384,
        provider: EmbeddingProvider | None = None,
        provider_name: str | None = None,
    ) -> None:
        self.provider = provider or self._build_provider(provider_name or settings.embedding_provider, dimension)

    def embed_text(self, text: str) -> List[float]:
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return run_provider_call(
            provider_policy("embedding", "embed_texts"),
            lambda: self.provider.embed_texts(texts),
        )

    def _build_provider(self, provider_name: str, dimension: int) -> EmbeddingProvider:
        normalized = provider_name.strip().lower()
        if normalized == "mock":
            return MockEmbeddingProvider(dimension=dimension)
        if normalized in {"openai", "openai-compatible", "dashscope"}:
            return OpenAICompatibleEmbeddingProvider()
        raise ValueError("EMBEDDING_PROVIDER must be 'mock', 'openai', 'openai-compatible', or 'dashscope'.")
