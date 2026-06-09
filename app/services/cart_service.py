"""Cart, address, and shadow checkout workflow service."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.core.providers import AppError
from app.core.transaction import unit_of_work
from app.models.cart import Address, Cart, CartItem, CheckoutSession
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.repositories.cart_repo import CartRepository
from app.repositories.order_repo import OrderRepository
from app.repositories.product_repo import ProductRepository
from app.schemas.cart import (
    AddressCreate,
    AddressListResponse,
    AddressRead,
    CartItemCreate,
    CartItemRead,
    CartItemUpdate,
    CartRead,
    CheckoutCreate,
    CheckoutRead,
)
from app.schemas.order import OrderRead
from app.services.policies.order_state_machine import FulfillmentStatus, PaymentStatus
from app.services.order_read_service import build_order_read, validate_purchasable_product


class CartService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.carts = CartRepository(db)
        self.products = ProductRepository(db)
        self.orders = OrderRepository(db)

    def get_cart(self, user_ref: str) -> CartRead:
        cart = self._get_or_create_cart(user_ref)
        return self._read_cart(cart)

    def create_item(self, payload: CartItemCreate, user_ref: str) -> CartRead:
        product = self._purchasable_product(payload.product_id)
        now = datetime.utcnow()
        cart = self._get_or_create_cart(user_ref, now=now)
        item = self.carts.get_item_by_product(cart.id, product.id)
        if item is None:
            item = self._build_item(cart.id, product, payload, now)
            self.carts.create_item(item)
        else:
            item.quantity = min(item.quantity + payload.quantity, 99)
            item.source_session_id = payload.source_session_id or item.source_session_id
            item.source_label = payload.source_label or item.source_label
            item.locked = item.locked or payload.locked
            item.updated_at = now
        cart.updated_at = now
        with unit_of_work(self.db) as uow:
            uow.refresh_after_commit(cart)
        return self._read_cart(cart)

    def update_item(self, item_id: int, payload: CartItemUpdate, user_ref: str) -> CartRead:
        now = datetime.utcnow()
        cart = self._get_or_create_cart(user_ref, now=now)
        item = self._get_cart_item(cart, item_id)
        item.quantity = payload.quantity
        item.updated_at = now
        cart.updated_at = now
        with unit_of_work(self.db) as uow:
            uow.refresh_after_commit(cart)
        return self._read_cart(cart)

    def delete_item(self, item_id: int, user_ref: str) -> CartRead:
        now = datetime.utcnow()
        cart = self._get_or_create_cart(user_ref, now=now)
        item = self._get_cart_item(cart, item_id)
        self.carts.delete_item(item)
        cart.updated_at = now
        with unit_of_work(self.db) as uow:
            uow.refresh_after_commit(cart)
        return self._read_cart(cart)

    def delete_item_at_position(self, position: int, user_ref: str) -> tuple[CartRead, str]:
        cart = self._get_or_create_cart(user_ref)
        items = self.carts.list_items(cart.id)
        if position < 1 or position > len(items):
            raise AppError("Cart item position not found", status_code=404, code="cart_item_position_not_found")
        removed_name = items[position - 1].name_snapshot
        return self.delete_item(items[position - 1].id, user_ref), removed_name

    def list_addresses(self, user_ref: str) -> AddressListResponse:
        return AddressListResponse(items=[AddressRead.model_validate(address) for address in self.carts.list_addresses(user_ref)])

    def create_address(self, payload: AddressCreate, user_ref: str) -> AddressRead:
        now = datetime.utcnow()
        make_default = payload.is_default or not self.carts.list_addresses(user_ref)
        if make_default:
            self.carts.update_addresses_clear_default(user_ref)
        address = Address(
            user_ref=user_ref,
            receiver_name=payload.receiver_name,
            phone=payload.phone,
            province=payload.province,
            city=payload.city,
            district=payload.district,
            detail=payload.detail,
            is_default=make_default,
            created_at=now,
            updated_at=now,
        )
        with unit_of_work(self.db) as uow:
            address = self.carts.create_address(address)
            uow.refresh_after_commit(address)
        return AddressRead.model_validate(address)

    def update_default_address(self, address_id: int, user_ref: str) -> AddressRead:
        now = datetime.utcnow()
        address = self.carts.get_address(user_ref, address_id)
        if address is None:
            raise AppError("Address not found", status_code=404, code="not_found")
        self.carts.update_addresses_clear_default(user_ref)
        address.is_default = True
        address.updated_at = now
        with unit_of_work(self.db) as uow:
            uow.refresh_after_commit(address)
        return AddressRead.model_validate(address)

    def create_checkout(self, payload: CheckoutCreate, user_ref: str) -> CheckoutRead:
        cart = self._get_or_create_cart(user_ref)
        items = self.carts.list_items(cart.id)
        if not items:
            raise AppError("Cart is empty", status_code=409, code="empty_cart")
        address = self._checkout_address(payload, user_ref)
        now = datetime.utcnow()
        address_snapshot = self._address_snapshot(address)
        cart_snapshot = self._cart_snapshot(cart, items)
        checkout = self._build_checkout(user_ref, cart.id, address_snapshot, cart_snapshot, payload.source_session_id, items, now)
        order = self._build_order(user_ref, checkout, address_snapshot, cart_snapshot, payload.source_session_id, now)
        order_items = [self._order_item_from_cart_item(item, now) for item in items]
        with unit_of_work(self.db) as uow:
            checkout = self.carts.create_checkout_session(checkout)
            order.checkout_session_id = checkout.id
            order = self.orders.create_with_items(order, order_items)
            checkout.order_id = order.id
            checkout.status = "ordered"
            checkout.updated_at = now
            self.carts.delete_items_for_cart(cart.id)
            cart.updated_at = now
            uow.refresh_after_commit(order)
        return CheckoutRead(checkout_session_id=checkout.id, order=self._read_order(order), cart_cleared=True)

    def _get_or_create_cart(self, user_ref: str, now: datetime | None = None) -> Cart:
        cart = self.carts.get_active_cart(user_ref)
        if cart is not None:
            return cart
        created_at = now or datetime.utcnow()
        cart = Cart(user_ref=user_ref, status="active", created_at=created_at, updated_at=created_at)
        self.carts.create_cart(cart)
        return cart

    def _get_cart_item(self, cart: Cart, item_id: int) -> CartItem:
        item = self.carts.get_item(cart.id, item_id)
        if item is None:
            raise AppError("Cart item not found", status_code=404, code="not_found")
        return item

    def _build_item(self, cart_id: int, product: Product, payload: CartItemCreate, now: datetime) -> CartItem:
        return CartItem(
            cart_id=cart_id,
            product_id=product.id,
            quantity=payload.quantity,
            unit_price_snapshot=Decimal(product.price),
            name_snapshot=product.name,
            image_url_snapshot=product.image_url,
            platform_snapshot=product.platform,
            product_url_snapshot=product.product_url,
            source_session_id=payload.source_session_id,
            source_label=payload.source_label,
            locked=payload.locked,
            created_at=now,
            updated_at=now,
        )

    def _checkout_address(self, payload: CheckoutCreate, user_ref: str) -> Address:
        if payload.address_id is not None:
            address = self.carts.get_address(user_ref, payload.address_id)
        elif payload.use_default_address:
            address = self.carts.get_default_address(user_ref)
        else:
            address = None
        if address is None:
            raise AppError("Default address is required", status_code=409, code="no_default_address")
        return address

    def _build_checkout(
        self,
        user_ref: str,
        cart_id: int,
        address_snapshot: dict[str, Any],
        cart_snapshot: dict[str, Any],
        source_session_id: str | None,
        items: list[CartItem],
        now: datetime,
    ) -> CheckoutSession:
        return CheckoutSession(
            user_ref=user_ref,
            cart_id=cart_id,
            order_id=None,
            status="created",
            address_snapshot=address_snapshot,
            cart_snapshot=cart_snapshot,
            total_price_snapshot=self._cart_total(items),
            source_session_id=source_session_id,
            created_at=now,
            updated_at=now,
        )

    def _build_order(
        self,
        user_ref: str,
        checkout: CheckoutSession,
        address_snapshot: dict[str, Any],
        cart_snapshot: dict[str, Any],
        source_session_id: str | None,
        now: datetime,
    ) -> Order:
        return Order(
            user_ref=user_ref,
            payment_status=PaymentStatus.PAID,
            fulfillment_status=FulfillmentStatus.PENDING,
            external_platform="buywise_shadow",
            external_order_ref=None,
            checkout_session_id=None,
            source_session_id=source_session_id,
            payment_mode="shadow_paid",
            address_snapshot=address_snapshot,
            cart_snapshot=cart_snapshot,
            total_price_snapshot=checkout.total_price_snapshot,
            paid_at=now,
            created_at=now,
            updated_at=now,
        )

    def _order_item_from_cart_item(self, item: CartItem, now: datetime) -> OrderItem:
        return OrderItem(
            order_id=0,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price_snapshot=item.unit_price_snapshot,
            name_snapshot=item.name_snapshot,
            platform_snapshot=item.platform_snapshot,
            product_url_snapshot=item.product_url_snapshot,
            feedback_due_at=None,
            created_at=now,
        )

    def _read_cart(self, cart: Cart) -> CartRead:
        items = [self._read_item(item) for item in self.carts.list_items(cart.id)]
        return CartRead(
            id=cart.id,
            user_ref=cart.user_ref,
            status=cart.status,
            total_quantity=sum(item.quantity for item in items),
            total_price=round(sum(item.line_total for item in items), 2),
            items=items,
            created_at=cart.created_at,
            updated_at=cart.updated_at,
        )

    def _read_item(self, item: CartItem) -> CartItemRead:
        unit_price = float(item.unit_price_snapshot)
        return CartItemRead(
            id=item.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price_snapshot=unit_price,
            line_total=round(unit_price * item.quantity, 2),
            name_snapshot=item.name_snapshot,
            image_url_snapshot=item.image_url_snapshot,
            platform_snapshot=item.platform_snapshot,
            product_url_snapshot=item.product_url_snapshot,
            source_session_id=item.source_session_id,
            source_label=item.source_label,
            locked=item.locked,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    def _read_order(self, order: Order) -> OrderRead:
        return build_order_read(order, self.orders.list_items(order.id))

    def _cart_snapshot(self, cart: Cart, items: list[CartItem]) -> dict[str, Any]:
        return {
            "cart_id": cart.id,
            "items": [
                {
                    "cart_item_id": item.id,
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price_snapshot),
                    "name": item.name_snapshot,
                }
                for item in items
            ],
            "total_price": float(self._cart_total(items)),
        }

    def _address_snapshot(self, address: Address) -> dict[str, Any]:
        return {
            "address_id": address.id,
            "receiver_name": address.receiver_name,
            "phone": address.phone,
            "province": address.province,
            "city": address.city,
            "district": address.district,
            "detail": address.detail,
        }

    def _cart_total(self, items: list[CartItem]) -> Decimal:
        return sum((item.unit_price_snapshot * item.quantity for item in items), Decimal("0"))

    def _purchasable_product(self, product_id: int) -> Product:
        return validate_purchasable_product(self.products.get_by_id(product_id))
