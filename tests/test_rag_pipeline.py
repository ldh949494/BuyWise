from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai.rag_pipeline import RAGPipeline
from app.core.database import Base
from app.models import Product
from app.schemas.chat import StructuredNeed


class FakeProductStore:
    def __init__(self, results):
        self.results = results
        self.queries = []

    def search(self, query: str, top_k: int = 10):
        self.queries.append({"query": query, "top_k": top_k})
        return self.results[:top_k]


def make_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return session_factory()


def seed_products(db):
    products = [
        Product(
            name="K87 静音红轴机械键盘",
            category="机械键盘",
            price=Decimal("329.00"),
            stock=10,
        ),
        Product(
            name="Gasket98 三模键盘",
            category="机械键盘",
            price=Decimal("599.00"),
            stock=8,
        ),
        Product(
            name="AirBuds Lite 蓝牙耳机",
            category="蓝牙耳机",
            price=Decimal("199.00"),
            stock=20,
        ),
        Product(
            name="Lite68 缺货键盘",
            category="机械键盘",
            price=Decimal("269.00"),
            stock=0,
        ),
        Product(
            name="NearBudget 静音键盘",
            category="机械键盘",
            price=Decimal("430.00"),
            stock=6,
        ),
        Product(
            name="FocusLamp 护眼台灯",
            category="台灯",
            price=Decimal("199.00"),
            stock=5,
        ),
    ]
    db.add_all(products)
    db.commit()
    return products


@pytest.mark.anyio
async def test_search_products_uses_vector_results_then_filters_rules() -> None:
    db = make_session()
    products = seed_products(db)
    store = FakeProductStore(
        [
            {"metadata": {"product_id": products[2].id}},
            {"metadata": {"product_id": products[1].id}},
            {"metadata": {"product_id": products[3].id}},
            {"metadata": {"product_id": products[0].id}},
        ]
    )
    pipeline = RAGPipeline(product_store=store)
    need = StructuredNeed(
        intent="recommend",
        category="机械键盘",
        budget_max=400,
        scenario="宿舍写代码",
        preferences=["静音"],
    )

    results = await pipeline.search_products(need, db, top_k=20)

    assert store.queries[0]["top_k"] == 60
    assert "机械键盘" in store.queries[0]["query"]
    assert [product.name for product in results] == ["K87 静音红轴机械键盘"]
    assert pipeline.last_diagnostics["retrieved_ids"] == [products[2].id, products[1].id, products[3].id, products[0].id]
    assert pipeline.last_diagnostics["final_ids"] == [products[0].id]


@pytest.mark.anyio
async def test_search_products_falls_back_to_repository_when_vector_store_empty() -> None:
    db = make_session()
    seed_products(db)
    store = FakeProductStore([])
    pipeline = RAGPipeline(product_store=store)
    need = {
        "intent": "recommend",
        "category": "机械键盘",
        "budget_max": 400,
    }

    results = await pipeline.search_products(need, db, top_k=20)

    assert [product.name for product in results] == ["K87 静音红轴机械键盘"]


@pytest.mark.anyio
async def test_search_products_runs_blocking_path_in_threadpool(monkeypatch) -> None:
    db = make_session()
    seed_products(db)
    store = FakeProductStore([])
    pipeline = RAGPipeline(product_store=store)
    calls = []

    async def fake_threadpool(func, *args, **kwargs):
        calls.append(func.__name__)
        return func(*args, **kwargs)

    monkeypatch.setattr("app.ai.rag_pipeline.run_blocking_io", fake_threadpool)

    await pipeline.search_products({"category": "机械键盘"}, db, top_k=20)

    assert calls == ["search_products_sync"]


@pytest.mark.anyio
async def test_search_products_falls_back_by_relaxing_budget_before_adjacent_category() -> None:
    db = make_session()
    products = seed_products(db)
    store = FakeProductStore([{"metadata": {"product_id": products[4].id}}])
    pipeline = RAGPipeline(product_store=store)
    need = StructuredNeed(
        intent="商品推荐",
        category="机械键盘",
        budget_max=400,
        scenario="宿舍",
        preferences=["低噪音"],
    )

    results = await pipeline.search_products(need, db, top_k=20)

    assert [product.name for product in results] == ["K87 静音红轴机械键盘", "NearBudget 静音键盘"]


@pytest.mark.anyio
async def test_search_products_uses_adjacent_category_after_strict_category_fails() -> None:
    db = make_session()
    seed_products(db)
    store = FakeProductStore([])
    pipeline = RAGPipeline(product_store=store)
    need = StructuredNeed(
        intent="商品推荐",
        category="学习用品",
        budget_max=100,
        scenario="学习",
        preferences=["护眼"],
    )

    results = await pipeline.search_products(need, db, top_k=1)

    assert [product.name for product in results] == ["FocusLamp 护眼台灯"]
