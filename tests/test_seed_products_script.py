from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models import Product
from app.scripts.demo_desktop_products import DEMO_DESKTOP_PRODUCTS
from app.scripts.demo_products import DEMO_SHOWCASE_PRODUCTS
from app.scripts.seed_products import ANDROID_CONTRACT_PRODUCTS, seed_products

COS_PREFIX = "https://buywise-1392410096.cos.ap-guangzhou.myqcloud.com/product-images/"


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

    expected_count = len(ANDROID_CONTRACT_PRODUCTS) + len(DEMO_SHOWCASE_PRODUCTS) + len(DEMO_DESKTOP_PRODUCTS)
    assert first_result == {"inserted": expected_count, "updated": 0}
    assert second_result == {"inserted": 0, "updated": expected_count}
    assert len(products) == expected_count
    product_by_id = {product.id: product for product in products}
    assert product_by_id[1105].category == "双肩包"
    assert product_by_id[1201].category == "电脑"
    assert product_by_id[1204].category == "显示器"
    assert product_by_id[1207].category == "鼠标"


def test_seed_product_profiles_use_real_cos_images() -> None:
    products = [*ANDROID_CONTRACT_PRODUCTS, *DEMO_SHOWCASE_PRODUCTS, *DEMO_DESKTOP_PRODUCTS]

    for product in products:
        assert product["product_url"].startswith("https://")
        assert "example.com" not in product["product_url"]
        assert product["image_url"].startswith(COS_PREFIX)
        assert product["image_url"] in product["image_urls"]
