"""Read-only closed beta operations summary for admin users."""

from __future__ import annotations

from typing import Any

from chromadb.errors import ChromaError
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.review import Review
from app.services.readiness_service import ProductStoreHealth, ReadinessService, validate_readiness
from app.vectorstore.chroma_client import ChromaProductStore


class AdminOpsService:
    def __init__(
        self,
        db: Session,
        *,
        readiness_service: ReadinessService | None = None,
        product_store: ProductStoreHealth | None = None,
    ) -> None:
        self.db = db
        self.readiness_service = readiness_service
        self.product_store = product_store

    def get_summary(self) -> dict[str, Any]:
        return {
            "readiness": self._readiness(),
            "index_health": self._index_health(),
            "catalog": self._catalog_metrics(),
            "token_guidance": self._token_guidance(),
            "operations": self._operations_status(),
            "recent_orders": self._recent_orders(),
            "pending_feedback": self._pending_feedback(),
            "recent_reviews": self._recent_reviews(),
        }

    def _readiness(self) -> dict[str, Any]:
        if self.readiness_service is None:
            return validate_readiness(include_details=True)
        return self.readiness_service.validate_readiness(include_details=True)

    def _index_health(self) -> dict[str, Any]:
        store = self.product_store or ChromaProductStore()
        close_store = self.product_store is None
        try:
            active_ids = set(self.db.scalars(select(Product.id).where(_active_filter())).all())
            indexed_ids = set(store.indexed_product_ids())
            return {
                "status": "ok" if active_ids <= indexed_ids else "attention",
                "collection_count": store.count(),
                "active_product_count": len(active_ids),
                "missing_product_ids": sorted(active_ids - indexed_ids),
                "stale_product_ids": sorted(indexed_ids - set(self.db.scalars(select(Product.id)).all())),
            }
        except (ChromaError, RuntimeError, ValueError, OSError) as exc:
            return {"status": "unavailable", "detail": str(exc)}
        finally:
            if close_store:
                close = getattr(store, "close", None)
                if callable(close):
                    close()

    def _catalog_metrics(self) -> dict[str, Any]:
        total = self.db.scalar(select(func.count()).select_from(Product)) or 0
        active = self.db.scalar(select(func.count()).select_from(Product).where(_active_filter())) or 0
        last_import = self.db.scalar(select(func.max(Product.created_at)))
        return {"total_products": total, "active_products": active, "last_catalog_change": last_import}

    def _token_guidance(self) -> list[dict[str, Any]]:
        configured = settings.configured_auth_api_keys.values()
        return [{"subject": item["subject"], "scopes": list(item["scopes"])} for item in configured]

    def _operations_status(self) -> list[dict[str, str]]:
        return [
            {
                "name": "真实目录导入",
                "status": "manual",
                "command": "python -m app.scripts.import_products --csv <beta-catalog.csv> --require-real-assets",
            },
            {
                "name": "商品索引重建",
                "status": "manual",
                "command": "python -m app.scripts.build_vector_index --mode rebuild",
            },
            {
                "name": "索引健康检查",
                "status": "read_only",
                "command": "python -m app.scripts.check_vector_index",
            },
        ]

    def _recent_orders(self) -> list[dict[str, Any]]:
        statement = select(Order).order_by(Order.created_at.desc(), Order.id.desc()).limit(20)
        return [self._order_payload(order) for order in self.db.scalars(statement).all()]

    def _pending_feedback(self) -> list[dict[str, Any]]:
        statement = (
            select(OrderItem, Order)
            .join(Order, Order.id == OrderItem.order_id)
            .where(OrderItem.feedback_due_at.is_not(None), OrderItem.feedback_submitted_at.is_(None))
            .order_by(OrderItem.feedback_due_at.asc(), OrderItem.id.asc())
            .limit(20)
        )
        return [self._feedback_payload(item, order) for item, order in self.db.execute(statement).all()]

    def _recent_reviews(self) -> list[dict[str, Any]]:
        statement = select(Review).order_by(Review.created_at.desc(), Review.id.desc()).limit(20)
        return [self._review_payload(review) for review in self.db.scalars(statement).all()]

    @staticmethod
    def _order_payload(order: Order) -> dict[str, Any]:
        return {
            "id": order.id,
            "user_ref": order.user_ref,
            "payment_status": order.payment_status,
            "fulfillment_status": order.fulfillment_status,
            "external_platform": order.external_platform,
            "external_order_ref": order.external_order_ref,
            "created_at": order.created_at,
        }

    @staticmethod
    def _feedback_payload(item: OrderItem, order: Order) -> dict[str, Any]:
        return {
            "order_id": order.id,
            "order_item_id": item.id,
            "user_ref": order.user_ref,
            "product_id": item.product_id,
            "product_name": item.name_snapshot,
            "feedback_due_at": item.feedback_due_at,
        }

    @staticmethod
    def _review_payload(review: Review) -> dict[str, Any]:
        return {
            "id": review.id,
            "product_id": review.product_id,
            "order_item_id": review.order_item_id,
            "user_ref": review.user_ref,
            "rating": float(review.rating) if review.rating is not None else None,
            "purchase_evidence": review.purchase_evidence,
            "status": review.status,
            "created_at": review.created_at,
        }


def _active_filter():
    return or_(Product.stock_status.is_(None), Product.stock_status != "discontinued")
