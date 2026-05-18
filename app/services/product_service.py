"""Product domain service."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.product import Product
from app.repositories.product_repo import ProductRepository
from app.schemas.product import ProductCreate
from app.utils.logging import get_logger


logger = get_logger(__name__)


class ProductService:
    def __init__(self, db: Session) -> None:
        self.repo = ProductRepository(db)

    def get_product(self, product_id: int) -> Product:
        product = self.repo.get_by_id(product_id)
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
        self._normalize_product(product)
        return product

    def get_products_by_ids(self, product_ids: list[int]) -> list[Product]:
        return self.repo.get_by_ids(product_ids)

    def list_products(
        self,
        category: str | None = None,
        keyword: str | None = None,
        price_min: float | None = None,
        price_max: float | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Product], int]:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        items, total = self.repo.list_products(
            category=category,
            keyword=keyword,
            price_min=price_min,
            price_max=price_max,
            page=page,
            page_size=page_size,
        )
        for product in items:
            self._normalize_product(product)
        logger.info(
            "Product list completed",
            extra={
                "category": category,
                "has_keyword": keyword is not None,
                "page": page,
                "page_size": page_size,
                "result_count": len(items),
                "total": total,
            },
        )
        return items, total

    def create_product(self, product_data: ProductCreate) -> Product:
        product = self.repo.create_product(product_data.model_dump(exclude_unset=True))
        self._normalize_product(product)
        logger.info(
            "Product created",
            extra={"product_id": product.id, "category": product.category},
        )
        return product

    def get_all_products(self) -> list[Product]:
        products = self.repo.get_all()
        for product in products:
            self._normalize_product(product)
        return products

    def _normalize_product(self, product: Product) -> None:
        if product.tags is None:
            product.tags = []
        if product.suitable_scene is None:
            product.suitable_scene = []
