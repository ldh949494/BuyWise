"""Cart, address, and shadow checkout API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status

from app.api.v1.orders import user_ref_from_request
from app.core.database import get_db
from app.schemas.cart import (
    AddressCreate,
    AddressListResponse,
    AddressRead,
    CartItemCreate,
    CartItemUpdate,
    CartRead,
    CheckoutCreate,
    CheckoutRead,
)
from app.services.cart_service import CartService


cart_router = APIRouter(prefix="/cart")
address_router = APIRouter(prefix="/addresses")


def get_cart_service(db=Depends(get_db)) -> CartService:
    return CartService(db)


@cart_router.get("", response_model=CartRead)
def get_cart(request: Request, service: CartService = Depends(get_cart_service)) -> CartRead:
    return service.get_cart(user_ref_from_request(request, ("orders:read",)))


@cart_router.post("/items", response_model=CartRead, status_code=status.HTTP_201_CREATED)
def add_cart_item(
    payload: CartItemCreate,
    request: Request,
    service: CartService = Depends(get_cart_service),
) -> CartRead:
    return service.create_item(payload, user_ref_from_request(request, ("orders:write",)))


@cart_router.patch("/items/{item_id}", response_model=CartRead)
def update_cart_item(
    item_id: int,
    payload: CartItemUpdate,
    request: Request,
    service: CartService = Depends(get_cart_service),
) -> CartRead:
    return service.update_item(item_id, payload, user_ref_from_request(request, ("orders:write",)))


@cart_router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cart_item(
    item_id: int,
    request: Request,
    service: CartService = Depends(get_cart_service),
) -> Response:
    service.delete_item(item_id, user_ref_from_request(request, ("orders:write",)))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@cart_router.post("/checkout", response_model=CheckoutRead, status_code=status.HTTP_201_CREATED)
def checkout_cart(
    payload: CheckoutCreate,
    request: Request,
    service: CartService = Depends(get_cart_service),
) -> CheckoutRead:
    return service.create_checkout(payload, user_ref_from_request(request, ("orders:write",)))


@address_router.get("", response_model=AddressListResponse)
def list_addresses(
    request: Request,
    service: CartService = Depends(get_cart_service),
) -> AddressListResponse:
    return service.list_addresses(user_ref_from_request(request, ("orders:read",)))


@address_router.post("", response_model=AddressRead, status_code=status.HTTP_201_CREATED)
def create_address(
    payload: AddressCreate,
    request: Request,
    service: CartService = Depends(get_cart_service),
) -> AddressRead:
    return service.create_address(payload, user_ref_from_request(request, ("orders:write",)))


@address_router.patch("/{address_id}/default", response_model=AddressRead)
def set_default_address(
    address_id: int,
    request: Request,
    service: CartService = Depends(get_cart_service),
) -> AddressRead:
    return service.update_default_address(address_id, user_ref_from_request(request, ("orders:write",)))
