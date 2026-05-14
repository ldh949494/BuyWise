from __future__ import annotations

import math
from typing import Any, List

from app.ai.embedding_client import EmbeddingClient
from app.core.config import settings


class ChromaProductStore:
    """In-memory Chroma-compatible product store for early RAG flows."""

    def __init__(
        self,
        persist_directory: str | None = None,
        embedding_client: EmbeddingClient | None = None,
    ) -> None:
        self.persist_directory = persist_directory or settings.chroma_persist_directory
        self.embedding_client = embedding_client or EmbeddingClient()
        self._documents: list[dict[str, Any]] = []

    def add_documents(self, docs: List[dict]) -> None:
        texts = [doc["text"] for doc in docs]
        embeddings = self.embedding_client.embed_texts(texts)

        for doc, embedding in zip(docs, embeddings):
            self._documents.append(
                {
                    "id": str(doc["id"]),
                    "text": doc["text"],
                    "metadata": doc.get("metadata", {}),
                    "embedding": embedding,
                }
            )

    def search(self, query: str, top_k: int = 10) -> List[dict]:
        if not self._documents:
            return []

        query_embedding = self.embedding_client.embed_text(query)
        ranked = sorted(
            self._documents,
            key=lambda doc: self._cosine_similarity(query_embedding, doc["embedding"]),
            reverse=True,
        )

        results = []
        for doc in ranked[:top_k]:
            score = self._cosine_similarity(query_embedding, doc["embedding"])
            results.append(
                {
                    "id": doc["id"],
                    "text": doc["text"],
                    "metadata": doc["metadata"],
                    "score": score,
                }
            )
        return results

    def reset(self) -> None:
        self._documents.clear()

    def _cosine_similarity(self, left: list[float], right: list[float]) -> float:
        if not left or not right:
            return 0.0
        dot = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return dot / (left_norm * right_norm)


class ChromaVectorStore:
    """Chroma wrapper placeholder for later embedding and retrieval flows."""

    def __init__(self, persist_directory: str | None = None) -> None:
        self.persist_directory = persist_directory or settings.chroma_persist_directory

    def similarity_search(self, query: str, top_k: int = 5) -> list[dict[str, object]]:
        store = ChromaProductStore(self.persist_directory)
        return store.search(query, top_k)
