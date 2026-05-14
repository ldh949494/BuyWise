"""Product API endpoints."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.product import ProductCreate, ProductListResponse, ProductRead
from app.services.product_service import ProductService


router = APIRouter(prefix="/products")


def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    return ProductService(db)


@router.get("", response_model=ProductListResponse)
def list_products(
    category: str | None = None,
    keyword: str | None = None,
    price_min: float | None = Query(default=None, ge=0),
    price_max: float | None = Query(default=None, ge=0),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: ProductService = Depends(get_product_service),
) -> ProductListResponse:
    items, total = service.list_products(
        category=category,
        keyword=keyword,
        price_min=price_min,
        price_max=price_max,
        page=page,
        page_size=page_size,
    )
    return ProductListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{product_id}", response_model=ProductRead)
def get_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
) -> ProductRead:
    return service.get_product(product_id)


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    product_data: ProductCreate,
    service: ProductService = Depends(get_product_service),
) -> ProductRead:
    return service.create_product(product_data)
