"""Feedback prompt workflow endpoints."""

from fastapi import APIRouter, Depends, Request, Response, status

from app.api.v1.orders import get_order_service, user_ref_from_request
from app.schemas.order import FeedbackPromptListResponse
from app.services.order_service import OrderService


router = APIRouter(prefix="/feedback")


@router.get("/prompts", response_model=FeedbackPromptListResponse)
def list_feedback_prompts(
    request: Request,
    service: OrderService = Depends(get_order_service),
) -> FeedbackPromptListResponse:
    return FeedbackPromptListResponse(items=service.list_due_feedback_prompts(user_ref_from_request(request)))


@router.post("/prompts/{order_item_id}/dismiss", status_code=status.HTTP_204_NO_CONTENT)
def dismiss_feedback_prompt(
    order_item_id: int,
    request: Request,
    service: OrderService = Depends(get_order_service),
) -> Response:
    service.update_feedback_prompt_dismissed(order_item_id, user_ref_from_request(request))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
