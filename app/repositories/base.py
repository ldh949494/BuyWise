from typing import Generic, TypeVar

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    """Base repository placeholder for future data access helpers."""
