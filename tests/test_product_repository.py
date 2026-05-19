from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models import Product
from app.repositories.product_repo import ProductRepository


def make_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


def seed_products(db):
    products = [
        Product(
            name="Phone Pro",
            category="phone",
            brand="Acme",
            price=Decimal("1999.00"),
            tags=["mobile"],
        ),
        Product(
            name="Office Laptop",
            category="computer",
            brand="Beta",
            price=Decimal("5999.00"),
            tags=["office"],
        ),
        Product(
            name="Phone Case",
            category="accessory",
            brand="Acme",
            price=Decimal("99.00"),
            description="Protective phone case",
        ),
    ]
    db.add_all(products)
    db.commit()
    return products


def test_product_repository_reads_by_id_and_ids() -> None:
    db = make_session()
    products = seed_products(db)
    repo = ProductRepository(db)

    found = repo.get_by_id(products[0].id)
    many = repo.get_by_ids([products[1].id, products[0].id, 999])

    assert found.name == "Phone Pro"
    assert [product.id for product in many] == [products[0].id, products[1].id]


def test_product_repository_lists_with_filters_and_pagination() -> None:
    db = make_session()
    seed_products(db)
    repo = ProductRepository(db)

    items, total = repo.list_products(
        category="phone",
        keyword="Pro",
        price_min=1000,
        price_max=3000,
        page=1,
        page_size=20,
    )

    assert total == 1
    assert [item.name for item in items] == ["Phone Pro"]


def test_product_repository_creates_and_returns_all_products() -> None:
    db = make_session()
    seed_products(db)
    repo = ProductRepository(db)

    created = repo.create_product({"name": "Tablet", "price": Decimal("2999.00")})
    all_products = repo.get_all()

    assert created.id is not None
    assert created.name == "Tablet"
    assert [product.name for product in all_products] == [
        "Phone Pro",
        "Office Laptop",
        "Phone Case",
        "Tablet",
    ]


def test_product_repository_create_flushes_without_committing() -> None:
    class FakeSession:
        def __init__(self) -> None:
            self.product = None
            self.committed = False
            self.flushed = False
            self.refreshed = False

        def add(self, product) -> None:
            self.product = product

        def flush(self) -> None:
            self.flushed = True
            self.product.id = 42

        def refresh(self, product) -> None:
            self.refreshed = product is self.product

        def commit(self) -> None:
            self.committed = True

    db = FakeSession()
    repo = ProductRepository(db)

    created = repo.create_product({"name": "Tablet", "price": Decimal("2999.00")})

    assert created.id == 42
    assert db.flushed is True
    assert db.refreshed is True
    assert db.committed is False
