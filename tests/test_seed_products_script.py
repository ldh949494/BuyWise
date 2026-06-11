from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models import Product
from app.scripts.seed_products import ANDROID_CONTRACT_PRODUCTS, DEMO_PROFILE_PRODUCTS, seed_products

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

    expected_count = len(DEMO_PROFILE_PRODUCTS)
    assert first_result == {"inserted": expected_count, "updated": 0}
    assert second_result == {"inserted": 0, "updated": expected_count}
    assert len(products) == expected_count
    product_by_id = {product.id: product for product in products}
    assert product_by_id[1105].category == "双肩包"
    assert product_by_id[1201].category == "电脑"
    assert product_by_id[1204].category == "显示器"
    assert product_by_id[1207].category == "鼠标"
    assert product_by_id[1301].category == "空气炸锅"
    assert product_by_id[1303].category == "吸尘器"
    assert product_by_id[1305].category == "投影仪"


def test_seed_product_profiles_use_real_cos_images() -> None:
    products = DEMO_PROFILE_PRODUCTS

    for product in products:
        assert product["product_url"].startswith("https://")
        assert "example.com" not in product["product_url"]
        assert product["image_url"].startswith(COS_PREFIX)
        assert product["image_url"] in product["image_urls"]
