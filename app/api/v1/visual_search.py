"""Hybrid visual search API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.visual_search import VisualSearchRequest, VisualSearchResponse
from app.services.visual_search_service import VisualSearchService


router = APIRouter(prefix="/visual-search")


def get_visual_search_service() -> VisualSearchService:
    return VisualSearchService()


@router.post("", response_model=VisualSearchResponse)
async def visual_search(
    payload: VisualSearchRequest,
    db: Session = Depends(get_db),
    service: VisualSearchService = Depends(get_visual_search_service),
) -> VisualSearchResponse:
    return await service.search(payload, db)
