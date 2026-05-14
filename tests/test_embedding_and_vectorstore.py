from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai.embedding_client import EmbeddingClient
from app.core.database import Base
from app.models import Product
from app.scripts.build_vector_index import build_vector_index
from app.vectorstore.chroma_client import ChromaProductStore


def make_session_factory():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def test_mock_embedding_client_returns_stable_fixed_dimension_vectors() -> None:
    client = EmbeddingClient(dimension=16)

    first = client.embed_text("静音机械键盘")
    second = client.embed_text("静音机械键盘")
    batch = client.embed_texts(["静音机械键盘", "蓝牙耳机"])

    assert len(first) == 16
    assert first == second
    assert len(batch) == 2
    assert all(len(vector) == 16 for vector in batch)
    assert batch[0] != batch[1]


def test_chroma_product_store_adds_searches_and_resets_documents() -> None:
    store = ChromaProductStore(embedding_client=EmbeddingClient(dimension=16))
    docs = [
        {
            "id": "product_1",
            "text": "商品名称：K87 静音红轴机械键盘\n类别：机械键盘",
            "metadata": {"product_id": 1, "category": "机械键盘", "price": 329},
        },
        {
            "id": "product_2",
            "text": "商品名称：AirBuds Lite 蓝牙耳机\n类别：蓝牙耳机",
            "metadata": {"product_id": 2, "category": "蓝牙耳机", "price": 199},
        },
    ]

    store.add_documents(docs)
    results = store.search("静音键盘", top_k=1)
    store.reset()

    assert len(results) == 1
    assert results[0]["id"] in {"product_1", "product_2"}
    assert "score" in results[0]
    assert "text" in results[0]
    assert "metadata" in results[0]
    assert store.search("静音键盘") == []


def test_build_vector_index_reads_products_and_writes_documents() -> None:
    session_factory = make_session_factory()
    with session_factory() as db:
        db.add_all(
            [
                Product(
                    name="K87 静音红轴机械键盘",
                    category="机械键盘",
                    brand="KeyNova",
                    price=Decimal("329.00"),
                    tags=["静音", "编程"],
                    suitable_scene=["宿舍", "写代码"],
                ),
                Product(
                    name="AirBuds Lite 蓝牙耳机",
                    category="蓝牙耳机",
                    brand="SoundAir",
                    price=Decimal("199.00"),
                ),
            ]
        )
        db.commit()

    store = ChromaProductStore(embedding_client=EmbeddingClient(dimension=16))
    result = build_vector_index(session_factory=session_factory, store=store)
    results = store.search("机械键盘", top_k=5)

    assert result == {"indexed": 2}
    assert len(results) == 2
    assert {item["metadata"]["product_id"] for item in results} == {1, 2}
