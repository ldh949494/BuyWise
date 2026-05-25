"""Simulated order API endpoints."""

from fastapi import APIRouter, Depends, Request, Response, status

from app.core.config import settings
from app.core.database import get_db
from app.core.providers import get_auth_provider
from app.schemas.order import OrderCreate, OrderListResponse, OrderRead
from app.services.order_service import OrderService, get_current_user_ref


router = APIRouter(prefix="/orders")


def user_ref_from_request(request: Request, required_scopes: tuple[str, ...] = ()) -> str:
    auth_provider = get_auth_provider()
    if settings.app_env == "prod":
        principal = auth_provider.require_principal(request, required_scopes)
    else:
        principal = auth_provider.get_current_principal(request)
    return get_current_user_ref(principal.subject if principal is not None else None)


def get_order_service(db=Depends(get_db)) -> OrderService:
    return OrderService(db)


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    request: Request,
    service: OrderService = Depends(get_order_service),
) -> OrderRead:
    return service.create_order(payload, user_ref_from_request(request, ("orders:write",)))


@router.get("", response_model=OrderListResponse)
def list_orders(
    request: Request,
    service: OrderService = Depends(get_order_service),
) -> OrderListResponse:
    return OrderListResponse(items=service.list_orders(user_ref_from_request(request, ("orders:read",))))


@router.get("/{order_id}", response_model=OrderRead)
def get_order(
    order_id: int,
    request: Request,
    service: OrderService = Depends(get_order_service),
) -> OrderRead:
    return service.get_order(order_id, user_ref_from_request(request, ("orders:read",)))


@router.post("/{order_id}/advance", response_model=OrderRead)
def advance_order(
    order_id: int,
    request: Request,
    service: OrderService = Depends(get_order_service),
) -> OrderRead:
    return service.update_order_progress(order_id, user_ref_from_request(request, ("orders:write",)))
