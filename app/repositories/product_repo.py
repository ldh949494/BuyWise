"""Product repository."""

from collections.abc import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.product import Product


class ProductRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, product_id: int) -> Product | None:
        return self.db.get(Product, product_id)

    def get_by_ids(self, product_ids: Sequence[int]) -> list[Product]:
        if not product_ids:
            return []

        statement = select(Product).where(Product.id.in_(product_ids)).order_by(Product.id)
        return list(self.db.scalars(statement).all())

    def list_products(
        self,
        category: str | None = None,
        keyword: str | None = None,
        price_min: float | None = None,
        price_max: float | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Product], int]:
        statement = select(Product)
        count_statement = select(func.count()).select_from(Product)

        filters = []
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
        self.db.commit()
        self.db.refresh(product)
        return product

    def get_all(self) -> list[Product]:
        statement = select(Product).order_by(Product.id)
        return list(self.db.scalars(statement).all())
