"""Readiness checks for closed beta deployment gates."""

from __future__ import annotations

from typing import Any

from chromadb.errors import ChromaError
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.product import Product
from app.repositories.product_repo import ProductRepository
from app.vectorstore.chroma_client import ChromaProductStore

CHECK_ORDER = ("config", "database", "products", "chroma", "vector_index")


def validate_readiness(include_details: bool = False, expected_active_products: int | None = None) -> dict[str, Any]:
    checks: dict[str, dict[str, Any]] = {}
    _run_config_check(checks, include_details)
    product_ids = _run_database_checks(checks, include_details, expected_active_products)
    _run_vector_checks(checks, product_ids, include_details)
    return _build_report(checks, include_details)


def _run_config_check(checks: dict[str, dict[str, Any]], include_details: bool) -> None:
    try:
        settings.validate_production()
        checks["config"] = _ok()
    except ValueError as exc:
        checks["config"] = _failed(exc, include_details)


def _run_database_checks(
    checks: dict[str, dict[str, Any]],
    include_details: bool,
    expected_active_products: int | None,
) -> set[int]:
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
            products = ProductRepository(db).get_all()
            product_ids = {product.id for product in products}
            product_count = len(product_ids)
            checks["database"] = _ok()
            details = {"product_count": product_count} if include_details else {}
            checks["products"] = _ok(details)
            if not product_ids:
                checks["products"] = _failed("No active products found.", include_details)
            elif expected_active_products is not None and product_count != expected_active_products:
                checks["products"] = _failed(
                    f"Expected {expected_active_products} active products, found {product_count}.",
                    include_details,
                    details,
                )
            return product_ids
    except SQLAlchemyError as exc:
        checks["database"] = _failed(exc, include_details)
        checks["products"] = _skipped()
        return set()


def _run_vector_checks(checks: dict[str, dict[str, Any]], product_ids: set[int], include_details: bool) -> None:
    if not product_ids:
        checks["chroma"] = _skipped()
        checks["vector_index"] = _skipped()
        return
    try:
        store = ChromaProductStore()
        indexed_ids = set(store.indexed_product_ids())
        missing = sorted(product_ids - indexed_ids)
        stale = _stale_active_index_ids(indexed_ids)
        checks["chroma"] = _ok({"collection_count": store.count()} if include_details else {})
        details = {"missing_in_index": missing, "stale_in_index": stale} if include_details else {}
        checks["vector_index"] = (
            _ok(details)
            if not missing and not stale
            else _failed("Vector index is incomplete.", include_details, details)
        )
    except (ChromaError, RuntimeError, ValueError, OSError) as exc:
        checks["chroma"] = _failed(exc, include_details)
        checks["vector_index"] = _skipped()


def _stale_active_index_ids(indexed_ids: set[int]) -> list[int]:
    if not indexed_ids:
        return []
    with SessionLocal() as db:
        db_ids = set(db.scalars(select(Product.id)).all())
    return sorted(indexed_ids - db_ids)


def _build_report(checks: dict[str, dict[str, Any]], include_details: bool) -> dict[str, Any]:
    ordered = {name: checks.get(name, _skipped()) for name in CHECK_ORDER}
    ready = all(check["status"] == "ok" for check in ordered.values())
    if include_details:
        return {"status": "ready" if ready else "not_ready", "service": "buywise-backend", "checks": ordered}
    return {
        "status": "ready" if ready else "not_ready",
        "service": "buywise-backend",
        "checks": {name: check["status"] for name, check in ordered.items()},
    }


def _ok(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"status": "ok", **(extra or {})}


def _skipped() -> dict[str, Any]:
    return {"status": "skipped"}


def _failed(
    error: BaseException | str,
    include_details: bool,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = {"status": "failed", **(extra or {})}
    if include_details:
        result["detail"] = str(error)
    return result
