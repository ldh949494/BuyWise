"""Conversational business action execution for chat."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from sqlalchemy.orm import Session

from app.core.providers import AppError
from app.schemas.cart import CartItemCreate, CheckoutCreate
from app.services.cart_service import CartService


@dataclass
class ChatActionResult:
    reply: str
    action: str
    data: dict[str, Any] = field(default_factory=dict)


class ChatActionService:
    ADD_MARKERS = ["加到购物车", "加入购物车", "加购", "放进购物车"]
    REMOVE_MARKERS = ["删掉", "删除", "移除", "去掉"]
    CHECKOUT_MARKERS = ["下单", "结算", "提交订单"]
    PLAN_MARKERS = ["整套", "这套", "方案", "清单"]
    ORDINALS = {
        "第一": 1,
        "第1": 1,
        "1": 1,
        "刚才": 1,
        "这款": 1,
        "那个": 1,
        "第二": 2,
        "第2": 2,
        "2": 2,
        "第三": 3,
        "第3": 3,
        "3": 3,
        "第四": 4,
        "第4": 4,
        "4": 4,
        "第五": 5,
        "第5": 5,
        "5": 5,
    }

    def handle_if_action(
        self,
        *,
        text: str,
        chat_repo: Any,
        session_id: str,
        db: Session,
        user_ref: str,
    ) -> ChatActionResult | None:
        normalized = text.strip()
        if not normalized or not hasattr(db, "add"):
            return None
        if self._contains(normalized, self.ADD_MARKERS):
            return self._add(normalized, chat_repo, session_id, db, user_ref)
        if self._contains(normalized, self.REMOVE_MARKERS):
            return self._remove(normalized, db, user_ref)
        if self._contains(normalized, self.CHECKOUT_MARKERS):
            return self._checkout(session_id, db, user_ref)
        return None

    def _add(self, text: str, chat_repo: Any, session_id: str, db: Session, user_ref: str) -> ChatActionResult:
        snapshot = self._latest_recommendation_snapshot(chat_repo, session_id)
        if snapshot is None:
            return ChatActionResult(reply="需要先完成一次导购推荐，我才能知道要把哪款加入购物车。", action="cart.add.needs_context")
        product_refs = self._resolve_product_refs(text, snapshot)
        if not product_refs:
            return ChatActionResult(reply="我没能确定要加哪款。可以说“把第一款加到购物车”。", action="cart.add.needs_reference")
        cart_service = CartService(db)
        cart = None
        for product_ref in product_refs:
            cart = cart_service.create_item(
                CartItemCreate(
                    product_id=int(product_ref["id"]),
                    quantity=self._quantity(text),
                    source_session_id=session_id,
                    source_label=product_ref.get("name"),
                ),
                user_ref,
            )
        names = "、".join(str(product.get("name") or f"商品{product['id']}") for product in product_refs[:3])
        count = len(product_refs)
        reply = f"已加入购物车：{names}。" if count == 1 else f"已把这套方案的 {count} 件商品加入购物车。"
        return ChatActionResult(reply=reply, action="cart.add", data={"cart": self._dump(cart), "product_ids": [item["id"] for item in product_refs]})

    def _remove(self, text: str, db: Session, user_ref: str) -> ChatActionResult:
        position = self._ordinal(text)
        cart, removed_name = CartService(db).delete_item_at_position(position, user_ref)
        return ChatActionResult(
            reply=f"已从购物车删除第 {position} 项：{removed_name}。",
            action="cart.remove",
            data={"cart": self._dump(cart), "position": position},
        )

    def _checkout(self, session_id: str, db: Session, user_ref: str) -> ChatActionResult:
        try:
            checkout = CartService(db).create_checkout(CheckoutCreate(use_default_address=True, source_session_id=session_id), user_ref)
        except AppError as exc:
            if exc.code == "no_default_address":
                return ChatActionResult(reply="下单前需要先设置默认地址。", action="checkout.needs_address")
            if exc.code == "empty_cart":
                return ChatActionResult(reply="购物车还是空的，先把想买的商品加入购物车。", action="checkout.empty_cart")
            raise
        return ChatActionResult(
            reply=f"已用默认地址生成影子订单：#{checkout.order.id}。",
            action="checkout.confirm",
            data={"checkout": self._dump(checkout)},
        )

    def _resolve_product_refs(self, text: str, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        if self._contains(text, self.PLAN_MARKERS) and snapshot.get("bundle_plans"):
            plan = self._plan_at(snapshot.get("bundle_plans") or [], self._ordinal(text))
            if plan is not None:
                return [
                    product
                    for item in plan.get("items", [])
                    if isinstance(item, dict)
                    for product in [item.get("product")]
                    if isinstance(product, dict) and product.get("id") is not None
                ]
        products = snapshot.get("products") or []
        if not products:
            products = self._products_from_bundle(snapshot)
        if not products:
            return []
        index = self._ordinal(text) - 1
        if index < 0 or index >= len(products):
            return []
        product = products[index]
        return [product] if isinstance(product, dict) and product.get("id") is not None else []

    def _latest_recommendation_snapshot(self, chat_repo: Any, session_id: str) -> dict[str, Any] | None:
        for message in reversed(chat_repo.list_messages(session_id, limit=20)):
            structured_data = getattr(message, "structured_data", None) or {}
            if structured_data.get("products") or structured_data.get("bundle_plans"):
                return structured_data
        return None

    def _products_from_bundle(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        products = []
        for plan in snapshot.get("bundle_plans") or []:
            for item in plan.get("items", []):
                product = item.get("product") if isinstance(item, dict) else None
                if isinstance(product, dict):
                    products.append(product)
        return products

    def _plan_at(self, plans: list[Any], ordinal: int) -> dict[str, Any] | None:
        index = max(ordinal - 1, 0)
        if index >= len(plans):
            index = 0
        plan = plans[index]
        return plan if isinstance(plan, dict) else None

    def _ordinal(self, text: str) -> int:
        for marker, value in self.ORDINALS.items():
            if marker in text:
                return value
        match = re.search(r"第?\s*(\d+)\s*(?:个|款|项|件|套)?", text)
        if match:
            return int(match.group(1))
        return 1

    def _quantity(self, text: str) -> int:
        match = re.search(r"(\d+)\s*(?:个|件|台|套)", text)
        if match:
            return min(max(int(match.group(1)), 1), 99)
        for marker, value in {"两个": 2, "两件": 2, "三件": 3, "三个": 3}.items():
            if marker in text:
                return value
        return 1

    def _contains(self, text: str, markers: list[str]) -> bool:
        return any(marker in text for marker in markers)

    def _dump(self, value: Any) -> Any:
        if hasattr(value, "model_dump"):
            return value.model_dump(mode="json")
        return value
