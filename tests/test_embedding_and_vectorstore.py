from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai.embedding_client import EmbeddingClient
from app.core.database import Base
from app.models import Product
from app.scripts.build_vector_index import build_vector_index
from app.services.product_index_service import validate_vector_index_health
from app.vectorstore.chroma_client import ChromaProductStore


def make_session_factory():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def make_store(tmp_path, collection_name: str = "test_products") -> ChromaProductStore:
    return ChromaProductStore(
        persist_directory=str(tmp_path),
        collection_name=collection_name,
        embedding_client=EmbeddingClient(dimension=16),
        batch_size=2,
    )


def seed_products(session_factory):
    with session_factory() as db:
        db.add_all(
            [
                Product(
                    name="K87 quiet keyboard",
                    category="keyboard",
                    brand="KeyNova",
                    price=Decimal("329.00"),
                    tags=["quiet", "wired"],
                    suitable_scene=["dorm", "coding"],
                ),
                Product(
                    name="AirBuds Lite",
                    category="headphones",
                    brand="SoundAir",
                    price=Decimal("199.00"),
                ),
            ]
        )
        db.commit()


def test_mock_embedding_client_returns_stable_fixed_dimension_vectors() -> None:
    client = EmbeddingClient(dimension=16)

    first = client.embed_text("quiet keyboard")
    second = client.embed_text("quiet keyboard")
    batch = client.embed_texts(["quiet keyboard", "wireless headphones"])

    assert len(first) == 16
    assert first == second
    assert len(batch) == 2
    assert all(len(vector) == 16 for vector in batch)
    assert batch[0] != batch[1]


def test_chroma_product_store_persists_documents_across_instances(tmp_path) -> None:
    first_store = make_store(tmp_path)
    first_store.add_documents(
        [
            {
                "id": "product_1",
                "text": "quiet keyboard for dorm coding",
                "metadata": {"product_id": 1, "name": "K87", "category": "keyboard", "price": 329},
            }
        ]
    )

    second_store = make_store(tmp_path)
    results = second_store.search("quiet keyboard", top_k=1)

    assert len(results) == 1
    assert results[0]["id"] == "product_1"
    assert results[0]["metadata"]["product_id"] == 1
    assert results[0]["metadata"]["name"] == "K87"
    assert "score" in results[0]
    assert "text" in results[0]


def test_chroma_product_store_upserts_and_resets_documents(tmp_path) -> None:
    store = make_store(tmp_path)
    store.add_documents(
        [
            {
                "id": "product_1",
                "text": "quiet keyboard",
                "metadata": {"product_id": 1, "name": "Old name"},
            }
        ]
    )
    store.add_documents(
        [
            {
                "id": "product_1",
                "text": "wireless headphones",
                "metadata": {"product_id": 1, "name": "New name"},
            }
        ]
    )

    results = store.search("wireless headphones", top_k=5)
    store.reset()

    assert len(results) == 1
    assert results[0]["metadata"]["name"] == "New name"
    assert store.search("wireless headphones") == []


def test_build_vector_index_rebuilds_all_products(tmp_path) -> None:
    session_factory = make_session_factory()
    seed_products(session_factory)

    store = make_store(tmp_path)
    result = build_vector_index(session_factory=session_factory, store=store)
    results = store.search("keyboard", top_k=5)

    assert result == {"indexed": 2, "mode": "rebuild", "deleted_collection": True}
    assert len(results) == 2
    assert {item["metadata"]["product_id"] for item in results} == {1, 2}
    assert {item["metadata"]["name"] for item in results} == {"K87 quiet keyboard", "AirBuds Lite"}


def test_build_vector_index_upserts_selected_product(tmp_path) -> None:
    session_factory = make_session_factory()
    seed_products(session_factory)

    store = make_store(tmp_path)
    result = build_vector_index(
        session_factory=session_factory,
        store=store,
        mode="upsert",
        product_ids=[2],
    )
    results = store.search("headphones", top_k=5)

    assert result == {"indexed": 1, "mode": "upsert", "deleted_collection": False}
    assert len(results) == 1
    assert results[0]["metadata"]["product_id"] == 2


def test_validate_vector_index_health_reports_missing_and_stale_ids(tmp_path) -> None:
    session_factory = make_session_factory()
    seed_products(session_factory)
    store = make_store(tmp_path)
    store.add_documents(
        [
            {
                "id": "product_1",
                "text": "quiet keyboard",
                "metadata": {"product_id": 1, "name": "K87"},
            },
            {
                "id": "product_999",
                "text": "stale product",
                "metadata": {"product_id": 999, "name": "Stale"},
            },
        ]
    )

    report = validate_vector_index_health(
        session_factory=session_factory,
        store=store,
        expected_product_ids=[1, 2],
        profile="test",
    )

    assert report["ok"] is False
    assert report["profile"] == "test"
    assert report["collection_count"] == 2
    assert report["db_product_count"] == 2
    assert report["missing_in_index"] == [2]
    assert report["stale_in_index"] == [999]
