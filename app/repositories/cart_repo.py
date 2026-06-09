"""Cart and address repositories."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cart import Address, Cart, CartItem, CheckoutSession


class CartRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_active_cart(self, user_ref: str) -> Cart | None:
        return self.db.scalar(select(Cart).where(Cart.user_ref == user_ref, Cart.status == "active"))

    def create_cart(self, cart: Cart) -> Cart:
        self.db.add(cart)
        self.db.flush()
        return cart

    def list_items(self, cart_id: int) -> list[CartItem]:
        statement = select(CartItem).where(CartItem.cart_id == cart_id).order_by(CartItem.created_at, CartItem.id)
        return list(self.db.scalars(statement).all())

    def get_item(self, cart_id: int, item_id: int) -> CartItem | None:
        return self.db.scalar(select(CartItem).where(CartItem.cart_id == cart_id, CartItem.id == item_id))

    def get_item_by_product(self, cart_id: int, product_id: int) -> CartItem | None:
        return self.db.scalar(select(CartItem).where(CartItem.cart_id == cart_id, CartItem.product_id == product_id))

    def create_item(self, item: CartItem) -> CartItem:
        self.db.add(item)
        self.db.flush()
        return item

    def delete_item(self, item: CartItem) -> None:
        self.db.delete(item)
        self.db.flush()

    def delete_items_for_cart(self, cart_id: int) -> None:
        for item in self.list_items(cart_id):
            self.db.delete(item)
        self.db.flush()

    def list_addresses(self, user_ref: str) -> list[Address]:
        statement = select(Address).where(Address.user_ref == user_ref).order_by(Address.is_default.desc(), Address.id)
        return list(self.db.scalars(statement).all())

    def get_address(self, user_ref: str, address_id: int) -> Address | None:
        return self.db.scalar(select(Address).where(Address.user_ref == user_ref, Address.id == address_id))

    def get_default_address(self, user_ref: str) -> Address | None:
        return self.db.scalar(select(Address).where(Address.user_ref == user_ref, Address.is_default.is_(True)))

    def create_address(self, address: Address) -> Address:
        self.db.add(address)
        self.db.flush()
        return address

    def update_addresses_clear_default(self, user_ref: str) -> None:
        for address in self.list_addresses(user_ref):
            address.is_default = False
        self.db.flush()

    def create_checkout_session(self, checkout: CheckoutSession) -> CheckoutSession:
        self.db.add(checkout)
        self.db.flush()
        return checkout
