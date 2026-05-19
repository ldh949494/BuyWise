"""RAG API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_rag_service
from app.schemas.rag import RagSearchRequest, RagSearchResponse
from app.services.rag_service import RagService


router = APIRouter(prefix="/rag")


@router.post("/search", response_model=RagSearchResponse)
def search_rag(
    request: RagSearchRequest,
    db: Session = Depends(get_db),
    service: RagService = Depends(get_rag_service),
) -> RagSearchResponse:
    return service.search(request, db)
