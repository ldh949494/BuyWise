from app.core.config import settings


class ChromaVectorStore:
    """Chroma wrapper placeholder for later embedding and retrieval flows."""

    def __init__(self, persist_directory: str | None = None) -> None:
        self.persist_directory = persist_directory or settings.chroma_persist_directory

    def similarity_search(self, query: str, top_k: int = 5) -> list[dict[str, object]]:
        _ = (query, top_k)
        return []
