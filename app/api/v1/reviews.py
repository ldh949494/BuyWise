"""Review API endpoints."""

from fastapi import APIRouter, Depends, Request, status

from app.api.v1.orders import user_ref_from_request
from app.core.database import get_db
from app.schemas.review import ReviewFromOrderItemCreate, ReviewRead, ReviewUpdate
from app.services.review_workflow_service import ReviewWorkflowService


router = APIRouter(prefix="/reviews")


def get_review_workflow_service(db=Depends(get_db)) -> ReviewWorkflowService:
    return ReviewWorkflowService(db)


@router.post("/from-order-item", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
def create_review_from_order_item(
    payload: ReviewFromOrderItemCreate,
    request: Request,
    service: ReviewWorkflowService = Depends(get_review_workflow_service),
) -> ReviewRead:
    return service.create_from_order_item(payload, user_ref_from_request(request, ("feedback:write",)))


@router.put("/{review_id}", response_model=ReviewRead)
def update_review(
    review_id: int,
    payload: ReviewUpdate,
    request: Request,
    service: ReviewWorkflowService = Depends(get_review_workflow_service),
) -> ReviewRead:
    return service.update_review(review_id, payload, user_ref_from_request(request, ("feedback:write",)))


@router.post("/{review_id}/withdraw", response_model=ReviewRead)
def withdraw_review(
    review_id: int,
    request: Request,
    service: ReviewWorkflowService = Depends(get_review_workflow_service),
) -> ReviewRead:
    return service.update_review_withdrawn(review_id, user_ref_from_request(request, ("feedback:write",)))
