from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models import Product
from app.schemas.visual_search import VisionRecognition, VisualMatch, VisualSearchRequest
from app.services.visual_search_service import VisualSearchService


class FakeVisionService:
    async def extract_image_info(self, image_url: str) -> dict:
        assert image_url == "/uploads/jacket.png"
        return {
            "category": "外套",
            "features": ["短款", "拉链"],
            "query": "黑色 短款 拉链 外套",
            "colors": ["黑色"],
            "materials": ["尼龙"],
            "shape": "短款",
            "style": "户外",
            "confidence": 0.9,
            "detected_objects": ["外套"],
        }


class FakeRAGPipeline:
    async def search_products(self, need, db, top_k=20):
        return [db.get(Product, 2)]


class FakeImageStore:
    def search_by_recognition(self, recognized: VisionRecognition, image_url: str, top_k: int):
        assert recognized.category == "外套"
        return [VisualMatch(product_id=1, image_url="https://cdn.example.test/jacket.jpg", score=0.91, source="test")]


@pytest.mark.anyio
async def test_visual_search_fuses_image_and_text_candidates() -> None:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with session_factory() as db:
        db.add_all(
            [
                Product(id=1, name="黑色短款尼龙外套", category="外套", price=Decimal("399.00"), tags=["黑色", "短款"]),
                Product(id=2, name="户外防风夹克", category="外套", price=Decimal("499.00"), tags=["户外", "拉链"]),
            ]
        )
        db.commit()
        service = VisualSearchService(
            vision_service=FakeVisionService(),
            rag_pipeline=FakeRAGPipeline(),
            image_store=FakeImageStore(),
        )

        response = await service.search(VisualSearchRequest(image_url="/uploads/jacket.png"), db)

    assert response.fallback_used is False
    assert [product.id for product in response.products] == [1, 2]
    assert response.visual_matches[0].product_id == 1
    assert any("商品图相似度" in reason for reason in response.match_reasons[1])
