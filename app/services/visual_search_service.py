"""Hybrid visual product search service."""

from __future__ import annotations

from typing import Any, Protocol

from sqlalchemy.orm import Session

from app.ai.rag_pipeline import RAGPipeline
from app.repositories.product_repo import ProductRepository
from app.schemas.chat import ProductCard, StructuredNeed
from app.schemas.visual_search import (
    VisionRecognition,
    VisualMatch,
    VisualSearchRequest,
    VisualSearchResponse,
)
from app.services.recommend_service import RecommendService
from app.services.vision_service import VisionService
from app.utils.logging import get_logger
from app.vectorstore.chroma_client import ChromaProductStore


logger = get_logger(__name__)


class ProductImageSearchGateway(Protocol):
    def search_by_recognition(self, recognized: VisionRecognition, image_url: str, top_k: int) -> list[VisualMatch]:
        ...


class ProductImageTextStore:
    """Product image search backed by textual image metadata in Chroma."""

    def __init__(self, store: ChromaProductStore | None = None) -> None:
        self.store = store or ChromaProductStore(collection_name="buywise_product_images")

    def search_by_recognition(self, recognized: VisionRecognition, image_url: str, top_k: int) -> list[VisualMatch]:
        _ = image_url
        query = build_visual_query(recognized)
        if not query:
            return []
        return [
            VisualMatch(
                product_id=int((result.get("metadata") or {}).get("product_id")),
                image_url=(result.get("metadata") or {}).get("image_url"),
                score=float(result.get("score") or 0),
                source="product_image_index",
            )
            for result in self.store.search(query, top_k=top_k)
            if (result.get("metadata") or {}).get("product_id") is not None
        ]


class VisualSearchService:
    def __init__(
        self,
        vision_service: VisionService | None = None,
        rag_pipeline: RAGPipeline | None = None,
        recommend_service: RecommendService | None = None,
        image_store: ProductImageSearchGateway | None = None,
    ) -> None:
        self.vision_service = vision_service or VisionService()
        self.rag_pipeline = rag_pipeline or RAGPipeline()
        self.recommend_service = recommend_service or RecommendService()
        self.image_store = image_store or ProductImageTextStore()

    async def search(self, request: VisualSearchRequest, db: Session) -> VisualSearchResponse:
        recognized, recognition_fallback_used = await self._recognize_or_fallback(request)
        need = self._need_from_recognition(recognized, request.message)
        visual_matches = [] if recognition_fallback_used else self._visual_matches(recognized, request.image_url, request.top_k)
        products = self._products_from_matches(db, visual_matches)
        rag_products = await self.rag_pipeline.search_products(need, db, top_k=request.top_k)
        merged = self._merge_products(products, rag_products)
        cards = self.recommend_service.rank(merged, need)[: request.top_k]
        reasons = {card.id: self._match_reasons(card, recognized, visual_matches) for card in cards}
        return VisualSearchResponse(
            recognized=recognized,
            products=cards,
            match_reasons=reasons,
            visual_matches=visual_matches,
            fallback_used=recognition_fallback_used or not visual_matches,
        )

    async def _recognize_or_fallback(self, request: VisualSearchRequest) -> tuple[VisionRecognition, bool]:
        try:
            recognized = VisionRecognition.model_validate(await self.vision_service.extract_image_info(request.image_url))
            return recognized, False
        except Exception:
            logger.error(
                "Visual recognition failed; falling back to text and catalog search",
                exc_info=True,
                extra={"top_k": request.top_k, "has_message": bool(request.message)},
            )
            return self._fallback_recognition(request.message), True

    def _fallback_recognition(self, message: str | None) -> VisionRecognition:
        query = message.strip() if message else None
        return VisionRecognition(
            category=None,
            features=[query] if query else [],
            query=query,
            colors=[],
            materials=[],
            shape=None,
            style=None,
            brand_cues=[],
            confidence=0.0,
            detected_objects=[],
        )

    def _visual_matches(self, recognized: VisionRecognition, image_url: str, top_k: int) -> list[VisualMatch]:
        try:
            return self.image_store.search_by_recognition(recognized, image_url, top_k)
        except (OSError, RuntimeError, TypeError, ValueError):
            return []

    def _products_from_matches(self, db: Session, visual_matches: list[VisualMatch]) -> list[Any]:
        ids = [match.product_id for match in visual_matches]
        return ProductRepository(db).get_by_ids(ids)

    def _merge_products(self, first: list[Any], second: list[Any]) -> list[Any]:
        merged = []
        seen = set()
        for product in [*first, *second]:
            product_id = getattr(product, "id", None)
            if product_id in seen:
                continue
            seen.add(product_id)
            merged.append(product)
        return merged

    def _need_from_recognition(self, recognized: VisionRecognition, message: str | None) -> StructuredNeed:
        preferences = [
            *recognized.features,
            *recognized.colors,
            *recognized.materials,
            *recognized.brand_cues,
        ]
        if recognized.shape:
            preferences.append(recognized.shape)
        if recognized.style:
            preferences.append(recognized.style)
        if message:
            preferences.append(message)
        return StructuredNeed(
            intent="visual_search",
            category=recognized.category,
            scenario=None,
            preferences=[item for item in preferences if item],
            retrieval_strategy="strict",
            need_clarify=False,
        )

    def _match_reasons(
        self,
        card: ProductCard,
        recognized: VisionRecognition,
        visual_matches: list[VisualMatch],
    ) -> list[str]:
        reasons = []
        visual_match = next((match for match in visual_matches if match.product_id == card.id), None)
        if visual_match is not None:
            reasons.append(f"商品图相似度 {visual_match.score:.2f}")
        for value in [*recognized.colors, *recognized.materials, recognized.shape, recognized.style]:
            if value and (value in card.name or value in card.tags):
                reasons.append(f"匹配视觉特征：{value}")
        if card.reason:
            reasons.append(card.reason)
        return reasons[:4]


def build_visual_query(recognized: VisionRecognition) -> str:
    parts = [
        recognized.query,
        recognized.category,
        recognized.shape,
        recognized.style,
        *recognized.features,
        *recognized.colors,
        *recognized.materials,
        *recognized.brand_cues,
        *recognized.detected_objects,
    ]
    return " ".join(str(part).strip() for part in parts if str(part or "").strip())
