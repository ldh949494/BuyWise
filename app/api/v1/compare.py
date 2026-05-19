"""Comparison API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_compare_service
from app.schemas.compare import CompareRequest, CompareResponse
from app.services.compare_service import CompareService


router = APIRouter(prefix="/products")


@router.post("/compare", response_model=CompareResponse)
async def compare_products(
    request: CompareRequest,
    db: Session = Depends(get_db),
    service: CompareService = Depends(get_compare_service),
) -> CompareResponse:
    return await service.compare(request.product_ids, request.user_need, db)
