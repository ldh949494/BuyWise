"""Product repository."""

from collections.abc import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.product import Product

DISCONTINUED_STOCK_STATUS = "discontinued"


class ProductRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, product_id: int, *, include_inactive: bool = False) -> Product | None:
        product = self.db.get(Product, product_id)
        if product is None:
            return None
        if not include_inactive and self._is_inactive(product):
            return None
        return product

    def get_by_ids(self, product_ids: Sequence[int], *, include_inactive: bool = False) -> list[Product]:
        if not product_ids:
            return []

        statement = select(Product).where(Product.id.in_(product_ids)).order_by(Product.id)
        if not include_inactive:
            statement = self._active_statement(statement)
        return list(self.db.scalars(statement).all())

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
        statement = select(Product)
        count_statement = select(func.count()).select_from(Product)

        filters = []
        if not include_inactive:
            filters.append(self._active_filter())
        if category:
            filters.append(Product.category == category)
        if keyword:
            pattern = f"%{keyword}%"
            filters.append(
                or_(
                    Product.name.ilike(pattern),
                    Product.description.ilike(pattern),
                    Product.brand.ilike(pattern),
                )
            )
        if price_min is not None:
            filters.append(Product.price >= price_min)
        if price_max is not None:
            filters.append(Product.price <= price_max)

        if filters:
            statement = statement.where(*filters)
            count_statement = count_statement.where(*filters)

        offset = (page - 1) * page_size
        statement = statement.order_by(Product.id).offset(offset).limit(page_size)

        total = self.db.scalar(count_statement) or 0
        items = list(self.db.scalars(statement).all())
        return items, total

    def create_product(self, product_data: dict) -> Product:
        product = Product(**product_data)
        self.db.add(product)
        self.db.flush()
        self.db.refresh(product)
        return product

    def update_product(self, product: Product, product_data: dict) -> Product:
        for key, value in product_data.items():
            setattr(product, key, value)
        self.db.flush()
        self.db.refresh(product)
        return product

    def get_by_sku(self, sku: str, *, include_inactive: bool = False) -> Product | None:
        statement = select(Product).where(Product.sku == sku)
        if not include_inactive:
            statement = self._active_statement(statement)
        return self.db.scalars(statement).first()

    def update_by_sku(self, product_data: dict) -> tuple[Product, bool]:
        sku = product_data.get("sku")
        product = self.get_by_sku(str(sku), include_inactive=True) if sku else None
        if product is None:
            return self.create_product(product_data), True
        return self.update_product(product, product_data), False

    def delete_product(self, product: Product) -> Product:
        product.stock_status = DISCONTINUED_STOCK_STATUS
        product.stock = 0
        self.db.flush()
        self.db.refresh(product)
        return product

    def get_all(self, *, include_inactive: bool = False) -> list[Product]:
        statement = select(Product).order_by(Product.id)
        if not include_inactive:
            statement = self._active_statement(statement)
        return list(self.db.scalars(statement).all())

    def _active_statement(self, statement):
        return statement.where(self._active_filter())

    def _active_filter(self):
        return or_(Product.stock_status.is_(None), Product.stock_status != DISCONTINUED_STOCK_STATUS)

    def _is_inactive(self, product: Product) -> bool:
        return product.stock_status == DISCONTINUED_STOCK_STATUS
