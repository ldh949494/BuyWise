"""Mirror product image URLs into Tencent COS and update product records."""

import argparse
import hashlib
import re
from dataclasses import dataclass
from io import BytesIO
from typing import Callable
from urllib.parse import unquote, urlparse

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.integrations.cos_storage_client import ObjectStorageClient, TencentCosStorageClient
from app.models import Product
from app.scripts.image_downloads import DownloadedImage, download_image
from app.scripts.job_artifacts import run_job_with_artifact


@dataclass
class MigrationSummary:
    products_seen: int = 0
    products_updated: int = 0
    urls_seen: int = 0
    urls_migrated: int = 0
    urls_skipped: int = 0
    urls_failed: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "products_seen": self.products_seen,
            "products_updated": self.products_updated,
            "urls_seen": self.urls_seen,
            "urls_migrated": self.urls_migrated,
            "urls_skipped": self.urls_skipped,
            "urls_failed": self.urls_failed,
        }


ImageDownloader = Callable[[str], DownloadedImage]


def migrate_product_images_to_cos(
    *,
    session_factory: Callable[[], Session] = SessionLocal,
    storage_client: ObjectStorageClient | None = None,
    downloader: ImageDownloader | None = None,
    dry_run: bool = True,
    include_cos_urls: bool = False,
    limit: int | None = None,
) -> MigrationSummary:
    """Copy product image URLs into COS and replace DB URLs with COS URLs."""
    summary = MigrationSummary()
    with session_factory() as db:
        _process_products(
            db,
            summary=summary,
            storage_client=_storage_client(storage_client, dry_run=dry_run),
            downloader=downloader or download_image,
            dry_run=dry_run,
            include_cos_urls=include_cos_urls,
            limit=limit,
        )
        _finish_session(db, dry_run=dry_run)
    return summary


def _storage_client(
    storage_client: ObjectStorageClient | None,
    *,
    dry_run: bool,
) -> ObjectStorageClient | None:
    return storage_client if dry_run else storage_client or TencentCosStorageClient()


def _process_products(
    db: Session,
    *,
    summary: MigrationSummary,
    storage_client: ObjectStorageClient | None,
    downloader: ImageDownloader,
    dry_run: bool,
    include_cos_urls: bool,
    limit: int | None,
) -> None:
    query = db.query(Product).order_by(Product.id)
    if limit is not None:
        query = query.limit(limit)
    for product in query.all():
        summary.products_seen += 1
        updated = _migrate_product_images(
            product,
            storage_client=storage_client,
            downloader=downloader,
            dry_run=dry_run,
            include_cos_urls=include_cos_urls,
            summary=summary,
        )
        if updated:
            summary.products_updated += 1


def _finish_session(db: Session, *, dry_run: bool) -> None:
    if dry_run:
        db.rollback()
    else:
        db.commit()


def _migrate_product_images(
    product: Product,
    *,
    storage_client: ObjectStorageClient | None,
    downloader: ImageDownloader,
    dry_run: bool,
    include_cos_urls: bool,
    summary: MigrationSummary,
) -> bool:
    replacements: dict[str, str] = {}
    for url in _product_image_urls(product):
        cos_url = _migrate_single_url(
            product,
            url,
            storage_client=storage_client,
            downloader=downloader,
            dry_run=dry_run,
            include_cos_urls=include_cos_urls,
            summary=summary,
        )
        if cos_url is not None:
            replacements[url] = cos_url
    if dry_run or not replacements:
        return bool(replacements)
    return _apply_replacements(product, replacements)


def _migrate_single_url(
    product: Product,
    url: str,
    *,
    storage_client: ObjectStorageClient | None,
    downloader: ImageDownloader,
    dry_run: bool,
    include_cos_urls: bool,
    summary: MigrationSummary,
) -> str | None:
    summary.urls_seen += 1
    if not _should_migrate_url(url, include_cos_urls=include_cos_urls):
        summary.urls_skipped += 1
        return None
    if dry_run:
        summary.urls_migrated += 1
        return url
    try:
        cos_url = _upload_url_to_cos(product, url, storage_client=storage_client, downloader=downloader)
        summary.urls_migrated += 1
        return cos_url
    except Exception:
        summary.urls_failed += 1
        return None


def _upload_url_to_cos(
    product: Product,
    url: str,
    *,
    storage_client: ObjectStorageClient | None,
    downloader: ImageDownloader,
) -> str:
    if storage_client is None:
        raise RuntimeError("COS storage client is required when dry_run is false.")
    image = downloader(url)
    key = _storage_key(product, url, image.suffix)
    return storage_client.upload_fileobj(
        key=key,
        fileobj=BytesIO(image.content),
        content_type=image.content_type,
    )


def _product_image_urls(product: Product) -> list[str]:
    urls = []
    if product.image_url:
        urls.append(product.image_url)
    if isinstance(product.image_urls, list):
        urls.extend(str(url) for url in product.image_urls if url)
    return list(dict.fromkeys(urls))


def _should_migrate_url(url: str, *, include_cos_urls: bool) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    return include_cos_urls or not _looks_like_cos_url(parsed.hostname or "")


def _looks_like_cos_url(host: str) -> bool:
    host = host.lower()
    configured_host = f"{settings.cos_bucket}.cos.{settings.cos_region}.myqcloud.com".lower()
    return host == configured_host or host.endswith(".myqcloud.com")


def _apply_replacements(product: Product, replacements: dict[str, str]) -> bool:
    changed = False
    if product.image_url in replacements:
        product.image_url = replacements[product.image_url]
        changed = True
    if isinstance(product.image_urls, list):
        image_urls = [replacements.get(str(url), str(url)) for url in product.image_urls]
        if image_urls != product.image_urls:
            product.image_urls = image_urls
            changed = True
    return changed


def _storage_key(product: Product, source_url: str, suffix: str) -> str:
    product_ref = _safe_path_part(product.sku or str(product.id))
    digest = hashlib.sha256(source_url.encode("utf-8")).hexdigest()[:16]
    stem = _safe_path_part(_source_stem(source_url)) or "image"
    return f"product-images/{product_ref}/{stem}-{digest}{suffix}"


def _source_stem(source_url: str) -> str:
    path = unquote(urlparse(source_url).path)
    filename = path.rsplit("/", 1)[-1]
    return filename.rsplit(".", 1)[0]


def _safe_path_part(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip())
    return cleaned.strip("-._")[:80]


def main() -> None:
    parser = argparse.ArgumentParser(description="Mirror product image URLs into Tencent COS.")
    parser.add_argument("--apply", action="store_true", help="Write migrated COS URLs back to the database.")
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N products.")
    parser.add_argument(
        "--include-cos-urls",
        action="store_true",
        help="Re-upload URLs that already look like Tencent COS URLs.",
    )
    parser.add_argument("--artifact-json", help="Optional path for a machine-readable job artifact.")
    args = parser.parse_args()

    inputs = {"apply": args.apply, "include_cos_urls": args.include_cos_urls, "limit": args.limit}
    summary = run_job_with_artifact(
        job_name="migrate_product_images_to_cos",
        inputs=inputs,
        artifact_path=args.artifact_json,
        action=lambda: migrate_product_images_to_cos(
            dry_run=not args.apply,
            include_cos_urls=args.include_cos_urls,
            limit=args.limit,
        ).as_dict(),
    )
    mode = "apply" if args.apply else "dry-run"
    print(f"{mode}: {summary}")


if __name__ == "__main__":
    main()
