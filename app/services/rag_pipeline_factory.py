"""RAG pipeline assembly for service-layer dependencies."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.rag_pipeline import RAGPipeline
from app.repositories.review_repo import ReviewRepository
from app.services.recommend_service import RecommendService
from app.services.review_signal_service import ReviewSignalService
from app.vectorstore.retrieval_gateway import VectorRetrievalGateway


def build_rag_pipeline(product_store: VectorRetrievalGateway | None = None) -> RAGPipeline:
    return RAGPipeline(
        product_store=product_store,
        reranker=RecommendService(),
        feedback_metrics_builder=_feedback_metrics,
    )


def _feedback_metrics(db: Session, product_ids: list[int]) -> dict[int, dict[str, object]]:
    return ReviewSignalService(ReviewRepository(db)).get_metrics_for_products(product_ids)
