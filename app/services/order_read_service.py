"""Shared order read-model helpers."""

from __future__ import annotations

from app.core.providers import AppError
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.schemas.order import OrderItemRead, OrderRead


def build_order_read(order: Order, items: list[OrderItem]) -> OrderRead:
    return OrderRead(
        id=order.id,
        user_ref=order.user_ref,
        payment_status=order.payment_status,
        fulfillment_status=order.fulfillment_status,
        external_platform=order.external_platform,
        external_order_ref=order.external_order_ref,
        checkout_session_id=order.checkout_session_id,
        source_session_id=order.source_session_id,
        payment_mode=order.payment_mode,
        address_snapshot=order.address_snapshot,
        cart_snapshot=order.cart_snapshot,
        total_price_snapshot=float(order.total_price_snapshot) if order.total_price_snapshot is not None else None,
        paid_at=order.paid_at,
        shipped_at=order.shipped_at,
        delivered_at=order.delivered_at,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=[OrderItemRead.model_validate(item) for item in items],
    )


def validate_purchasable_product(product: Product | None) -> Product:
    if product is None:
        raise AppError("Product not found", status_code=404, code="not_found")
    if product.stock_status == "out_of_stock":
        raise AppError("Product is out of stock", status_code=409, code="out_of_stock")
    if product.price is None:
        raise AppError("Product price is required", status_code=409, code="missing_price")
    return product
