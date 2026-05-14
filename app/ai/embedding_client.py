"""Embedding client."""

from __future__ import annotations

import hashlib
import math
import random
from typing import List


class EmbeddingClient:
    """Mock embedding client with stable fixed-dimension vectors."""

    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension

    def embed_text(self, text: str) -> List[float]:
        seed = int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")
        generator = random.Random(seed)
        vector = [generator.uniform(-1.0, 1.0) for _ in range(self.dimension)]
        return self._normalize(vector)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(text) for text in texts]

    def _normalize(self, vector: list[float]) -> list[float]:
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]
