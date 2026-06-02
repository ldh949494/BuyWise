"""Vector retrieval gateway protocol."""

from __future__ import annotations

from typing import Any, Protocol


class VectorRetrievalGateway(Protocol):
    def add_documents(self, docs: list[dict]) -> None:
        ...

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        ...

    def reset(self) -> None:
        ...

    def delete_product_documents(self, product_id: int) -> None:
        ...

    def count(self) -> int:
        ...

    def indexed_product_ids(self) -> list[int]:
        ...

    def indexed_product_metadata(self) -> list[dict[str, Any]]:
        ...
