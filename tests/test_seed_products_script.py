from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models import Product
from app.scripts.demo_products import DEMO_SHOWCASE_PRODUCTS
from app.scripts.seed_products import ANDROID_CONTRACT_PRODUCTS, seed_products


def make_session_factory():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def test_seed_products_default_profile_keeps_android_contract_scope() -> None:
    session_factory = make_session_factory()

    result = seed_products(session_factory=session_factory)

    with session_factory() as db:
        products = db.query(Product).order_by(Product.id).all()

    assert result == {"inserted": len(ANDROID_CONTRACT_PRODUCTS), "updated": 0}
    assert [product.id for product in products] == [1001, 1002, 1003, 1004, 1005]


def test_seed_products_demo_profile_upserts_showcase_products() -> None:
    session_factory = make_session_factory()

    first_result = seed_products(session_factory=session_factory, profile="demo")
    second_result = seed_products(session_factory=session_factory, profile="demo")

    with session_factory() as db:
        products = db.query(Product).order_by(Product.id).all()

    expected_count = len(ANDROID_CONTRACT_PRODUCTS) + len(DEMO_SHOWCASE_PRODUCTS)
    assert first_result == {"inserted": expected_count, "updated": 0}
    assert second_result == {"inserted": 0, "updated": expected_count}
    assert len(products) == expected_count
    assert products[-1].id == 1105
    assert products[-1].category == "双肩包"
