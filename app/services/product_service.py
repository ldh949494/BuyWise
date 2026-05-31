"""Product domain service."""

from collections.abc import Callable

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.providers import AppError
from app.core.transaction import unit_of_work
from app.models.product import Product
from app.repositories.price_repo import PriceHistoryRepository
from app.repositories.product_repo import ProductRepository
from app.repositories.review_repo import ReviewRepository
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.product_index_service import update_product_index
from app.services.review_signal_service import ReviewSignalService
from app.utils.logging import get_logger


logger = get_logger(__name__)
IndexUpdater = Callable[[list[int]], dict[str, int | str | bool]]


class ProductService:
    def __init__(self, db: Session, index_updater: IndexUpdater | None = update_product_index) -> None:
        self.db = db
        self.repo = ProductRepository(db)
        self.price_repo = PriceHistoryRepository(db)
        self.review_repo = ReviewRepository(db)
        self.index_updater = index_updater

    def get_product(self, product_id: int, *, include_inactive: bool = False) -> Product:
        product = self.repo.get_by_id(product_id, include_inactive=include_inactive)
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
        product.feedback_metrics = ReviewSignalService(self.review_repo).get_metrics_for_products([product.id]).get(product.id, {})
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
        include_inactive: bool = False,
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
            include_inactive=include_inactive,
        )
        for product in items:
            self._normalize_product(product)
        self._log_product_list(category, keyword, page, page_size, len(items), total)
        return items, total

    def create_product(self, product_data: ProductCreate) -> Product:
        with unit_of_work(self.db) as uow:
            product = self.repo.create_product(product_data.model_dump(exclude_unset=True))
            uow.refresh_after_commit(product)
        return self._after_write_commit(product, operation="create")

    def update_product(self, product_id: int, product_data: ProductUpdate) -> Product:
        product = self._active_product(product_id)
        with unit_of_work(self.db) as uow:
            payload = product_data.model_dump(exclude_unset=True)
            product = self.repo.update_product(product, payload)
            uow.refresh_after_commit(product)
        return self._after_write_commit(product, operation="update")

    def delete_product(self, product_id: int) -> Product:
        product = self._active_product(product_id)
        with unit_of_work(self.db) as uow:
            product = self.repo.delete_product(product)
            uow.refresh_after_commit(product)
        return self._after_write_commit(product, operation="soft_delete")

    def update_product_by_sku(self, product_data: dict) -> tuple[Product, bool]:
        with unit_of_work(self.db) as uow:
            product, inserted = self.repo.update_by_sku(product_data)
            uow.refresh_after_commit(product)
        product = self._after_write_commit(product, operation="upsert")
        return product, inserted

    def get_all_products(self) -> list[Product]:
        products = self.repo.get_all()
        for product in products:
            self._normalize_product(product)
        return products

    def _active_product(self, product_id: int) -> Product:
        product = self.repo.get_by_id(product_id)
        if product is None:
            raise AppError("Product not found", status_code=404, code="not_found")
        return product

    def _after_write_commit(self, product: Product, *, operation: str) -> Product:
        self._normalize_product(product)
        self._upsert_index_best_effort(product.id, operation)
        logger.info(
            "Product write completed",
            extra={
                "product_id": product.id,
                "category": product.category,
                "operation": operation,
                "stock_status": product.stock_status,
            },
        )
        return product

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
        if not hasattr(product, "feedback_metrics"):
            product.feedback_metrics = {}

    def _stock_status(self, stock: int | None) -> str | None:
        if stock is None:
            return None
        if stock <= 0:
            return "out_of_stock"
        if stock <= 5:
            return "low_stock"
        return "in_stock"

    def _upsert_index_best_effort(self, product_id: int, operation: str) -> None:
        if self.index_updater is None:
            return
        try:
            self.index_updater([product_id])
            logger.info(
                "Product index upsert completed",
                extra={"product_id": product_id, "operation": operation},
            )
        except (RuntimeError, ValueError, SQLAlchemyError):
            logger.exception(
                "Product index upsert failed",
                extra={
                    "product_id": product_id,
                    "operation": operation,
                    "index_status": "failed",
                },
            )

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
