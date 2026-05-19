"""Product domain service."""

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.product import Product
from app.repositories.price_repo import PriceHistoryRepository
from app.repositories.product_repo import ProductRepository
from app.repositories.review_repo import ReviewRepository
from app.schemas.product import ProductCreate
from app.utils.logging import get_logger


logger = get_logger(__name__)


class ProductService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProductRepository(db)
        self.price_repo = PriceHistoryRepository(db)
        self.review_repo = ReviewRepository(db)

    def get_product(self, product_id: int) -> Product:
        product = self.repo.get_by_id(product_id)
        if product is None:
            raise AppError(
                "Product not found",
                status_code=404,
                code="not_found",
            )
        self._normalize_product(product)
        product.price_history = self.price_repo.list_for_product(product.id)
        if not product.review_summary:
            product.review_summary = self.review_repo.build_summary_for_product(product.id)
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
        self._log_product_list(category, keyword, page, page_size, len(items), total)
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
        if product.image_urls is None:
            product.image_urls = []
        if product.stock_status is None:
            product.stock_status = self._stock_status(product.stock)
        if not hasattr(product, "price_history"):
            product.price_history = []

    def _stock_status(self, stock: int | None) -> str | None:
        if stock is None:
            return None
        if stock <= 0:
            return "out_of_stock"
        if stock <= 5:
            return "low_stock"
        return "in_stock"

    def _log_product_list(
        self,
        category: str | None,
        keyword: str | None,
        page: int,
        page_size: int,
        result_count: int,
        total: int,
    ) -> None:
        logger.info(
            "Product list completed",
            extra={
                "category": category,
                "has_keyword": keyword is not None,
                "page": page,
                "page_size": page_size,
                "result_count": result_count,
                "total": total,
            },
        )
