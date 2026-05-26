"""Admin product management endpoints."""

from fastapi import APIRouter, Depends, Query, status

from app.core.admin_auth import AdminPrincipal, require_admin
from app.core.dependencies import get_product_service
from app.schemas.admin import AdminProductWriteResponse
from app.schemas.product import ProductCreate, ProductListResponse, ProductRead, ProductUpdate
from app.services.product_service import ProductService


router = APIRouter(prefix="/products")


@router.get("", response_model=ProductListResponse)
def list_admin_products(
    category: str | None = None,
    keyword: str | None = None,
    price_min: float | None = Query(default=None, ge=0),
    price_max: float | None = Query(default=None, ge=0),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: ProductService = Depends(get_product_service),
    principal: AdminPrincipal = Depends(require_admin),
) -> ProductListResponse:
    _ = principal
    items, total = service.list_products(
        category=category,
        keyword=keyword,
        price_min=price_min,
        price_max=price_max,
        page=page,
        page_size=page_size,
        include_inactive=True,
    )
    return ProductListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{product_id}", response_model=ProductRead)
def get_admin_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
    principal: AdminPrincipal = Depends(require_admin),
) -> ProductRead:
    _ = principal
    return service.get_product(product_id, include_inactive=True)


@router.post("", response_model=AdminProductWriteResponse, status_code=status.HTTP_201_CREATED)
def create_admin_product(
    product_data: ProductCreate,
    service: ProductService = Depends(get_product_service),
    principal: AdminPrincipal = Depends(require_admin),
) -> AdminProductWriteResponse:
    _ = principal
    product = service.create_product(product_data)
    return AdminProductWriteResponse(product=product)


@router.patch("/{product_id}", response_model=AdminProductWriteResponse)
def update_admin_product(
    product_id: int,
    product_data: ProductUpdate,
    service: ProductService = Depends(get_product_service),
    principal: AdminPrincipal = Depends(require_admin),
) -> AdminProductWriteResponse:
    _ = principal
    product = service.update_product(product_id, product_data)
    return AdminProductWriteResponse(product=product)


@router.delete("/{product_id}", response_model=AdminProductWriteResponse)
def delete_admin_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
    principal: AdminPrincipal = Depends(require_admin),
) -> AdminProductWriteResponse:
    _ = principal
    product = service.delete_product(product_id)
    return AdminProductWriteResponse(product=product)
