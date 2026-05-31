from __future__ import annotations

from typing import Any, List

import chromadb

from app.ai.embedding_client import EmbeddingClient
from app.core.config import settings
from app.core.resilience import provider_policy, run_provider_call


class ChromaProductStore:
    """Persistent ChromaDB-backed product vector store."""

    def __init__(
        self,
        persist_directory: str | None = None,
        embedding_client: EmbeddingClient | None = None,
        collection_name: str | None = None,
        batch_size: int = 100,
    ) -> None:
        self.persist_directory = persist_directory or settings.chroma_persist_directory
        self.embedding_client = embedding_client or EmbeddingClient()
        self.collection_name = collection_name or settings.chroma_product_collection
        self.batch_size = batch_size
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self._get_or_create_collection()

    def add_documents(self, docs: List[dict]) -> None:
        for batch in self._iter_batches(docs):
            texts = [doc["text"] for doc in batch]
            embeddings = self.embedding_client.embed_texts(texts)
            run_provider_call(
                provider_policy("chroma", "upsert"),
                lambda batch=batch, texts=texts, embeddings=embeddings: self.collection.upsert(
                    ids=[str(doc["id"]) for doc in batch],
                    documents=texts,
                    metadatas=[self._clean_metadata(doc.get("metadata", {})) for doc in batch],
                    embeddings=embeddings,
                ),
            )

    def search(self, query: str, top_k: int = 10) -> List[dict]:
        if top_k <= 0 or self.count() == 0:
            return []

        query_embedding = self.embedding_client.embed_text(query)
        result = run_provider_call(
            provider_policy("chroma", "query"),
            lambda: self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            ),
        )

        results = []
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        for doc_id, text, metadata, distance in zip(ids, documents, metadatas, distances):
            results.append(
                {
                    "id": doc_id,
                    "text": text,
                    "metadata": metadata or {},
                    "score": self._score_from_distance(distance),
                }
            )
        return results

    def reset(self) -> None:
        try:
            run_provider_call(
                provider_policy("chroma", "delete_collection"),
                lambda: self.client.delete_collection(self.collection_name),
            )
        except ValueError:
            pass
        self.collection = self._get_or_create_collection()

    def count(self) -> int:
        return int(run_provider_call(provider_policy("chroma", "count"), self.collection.count))

    def indexed_product_ids(self) -> list[int]:
        if self.count() == 0:
            return []
        result = run_provider_call(
            provider_policy("chroma", "get_indexed_product_ids"),
            lambda: self.collection.get(include=["metadatas"]),
        )
        product_ids = []
        for metadata in result.get("metadatas", []):
            if not metadata or metadata.get("product_id") is None:
                continue
            product_ids.append(int(metadata["product_id"]))
        return sorted(set(product_ids))

    def _get_or_create_collection(self):
        return run_provider_call(
            provider_policy("chroma", "get_or_create_collection"),
            lambda: self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            ),
        )

    def _iter_batches(self, docs: List[dict]) -> list[List[dict]]:
        batch_size = max(1, self.batch_size)
        return [docs[index : index + batch_size] for index in range(0, len(docs), batch_size)]

    def _clean_metadata(self, metadata: dict[str, Any]) -> dict[str, str | int | float | bool]:
        return {
            key: value
            for key, value in metadata.items()
            if isinstance(value, (str, int, float, bool))
        }

    def _score_from_distance(self, distance: float | None) -> float:
        if distance is None:
            return 0.0
        return max(0.0, 1.0 - float(distance))


class ChromaVectorStore:
    """Chroma wrapper placeholder for later embedding and retrieval flows."""

    def __init__(self, persist_directory: str | None = None) -> None:
        self.persist_directory = persist_directory or settings.chroma_persist_directory

    def similarity_search(self, query: str, top_k: int = 5) -> list[dict[str, object]]:
        store = ChromaProductStore(persist_directory=self.persist_directory)
        return store.search(query, top_k)
