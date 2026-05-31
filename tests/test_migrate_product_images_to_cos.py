from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import Product
from app.scripts.migrate_product_images_to_cos import DownloadedImage, migrate_product_images_to_cos


class FakeStorageClient:
    def __init__(self) -> None:
        self.calls = []

    def upload_fileobj(self, *, key, fileobj, content_type):
        self.calls.append((key, fileobj.read(), content_type))
        return f"https://cos.example.com/{key}"


def make_session_factory():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def test_migrate_product_images_to_cos_updates_product_image_urls() -> None:
    session_factory = make_session_factory()
    with session_factory() as db:
        db.add(
            Product(
                id=1,
                sku="demo-keyboard",
                name="Demo Keyboard",
                image_url="https://source.example.com/images/main.jpg",
                image_urls=[
                    "https://source.example.com/images/main.jpg",
                    "https://source.example.com/images/alt.webp",
                ],
            )
        )
        db.commit()

    def downloader(url: str) -> DownloadedImage:
        suffix = ".webp" if url.endswith(".webp") else ".jpg"
        content_type = "image/webp" if suffix == ".webp" else "image/jpeg"
        return DownloadedImage(content=f"bytes:{url}".encode(), content_type=content_type, suffix=suffix)

    storage = FakeStorageClient()
    summary = migrate_product_images_to_cos(
        session_factory=session_factory,
        storage_client=storage,
        downloader=downloader,
        dry_run=False,
    )

    with session_factory() as db:
        product = db.get(Product, 1)
        assert product is not None
        assert product.image_url.startswith("https://cos.example.com/product-images/demo-keyboard/main-")
        assert product.image_urls[0] == product.image_url
        assert product.image_urls[1].startswith("https://cos.example.com/product-images/demo-keyboard/alt-")
    assert summary.as_dict() == {
        "products_seen": 1,
        "products_updated": 1,
        "urls_seen": 2,
        "urls_migrated": 2,
        "urls_skipped": 0,
        "urls_failed": 0,
    }
    assert len(storage.calls) == 2


def test_migrate_product_images_to_cos_dry_run_does_not_upload_or_update() -> None:
    session_factory = make_session_factory()
    with session_factory() as db:
        db.add(
            Product(
                id=1,
                sku="demo-keyboard",
                name="Demo Keyboard",
                image_url="https://source.example.com/images/main.jpg",
            )
        )
        db.commit()

    def downloader(_: str) -> DownloadedImage:
        raise AssertionError("dry-run should not download images")

    storage = FakeStorageClient()
    summary = migrate_product_images_to_cos(
        session_factory=session_factory,
        storage_client=storage,
        downloader=downloader,
        dry_run=True,
    )

    with session_factory() as db:
        product = db.get(Product, 1)
        assert product is not None
        assert product.image_url == "https://source.example.com/images/main.jpg"
    assert summary.urls_migrated == 1
    assert storage.calls == []
