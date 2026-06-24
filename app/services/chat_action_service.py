"""Conversational business action execution for chat."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import re
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.metrics import count_agent_action
from app.core.providers import AppError
from app.models.agent_action import AgentAction
from app.repositories.agent_action_repo import AgentActionRepository
from app.schemas.cart import CartItemCreate, CheckoutCreate
from app.services.cart_service import CartService


@dataclass
class ChatActionResult:
    reply: str
    action: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ChatActionContext:
    session_id: str
    user_ref: str
    owner_subject: str | None
    owner_auth_type: str | None


class ChatActionService:
    ADD_MARKERS = ["加到购物车", "加入购物车", "加购", "放进购物车"]
    REMOVE_MARKERS = ["删掉", "删除", "移除", "去掉"]
    CHECKOUT_MARKERS = ["下单", "结算", "提交订单"]
    CONFIRM_MARKERS = ["确认", "确认执行"]
    PLAN_MARKERS = ["整套", "这套", "方案", "清单"]
    EXPLICIT_PRODUCT_REFERENCE_MARKERS = [
        "刚才",
        "这款",
        "这件",
        "这个",
        "这一个",
        "它",
        "首推",
        "第一",
        "第二",
        "第三",
        "第四",
        "第五",
        "第1",
        "第2",
        "第3",
        "第4",
        "第5",
    ]
    EXPLICIT_PLAN_REFERENCE_MARKERS = ["整套", "这套", "第一套", "第二套", "第三套", "第1套", "第2套", "第3套", "方案一", "方案二", "方案三"]
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
        owner_subject: str | None = None,
        owner_auth_type: str | None = None,
    ) -> ChatActionResult | None:
        normalized = text.strip()
        if not normalized or not hasattr(db, "add"):
            return None
        context = ChatActionContext(session_id, user_ref, owner_subject, owner_auth_type)
        if self._contains(normalized, self.CONFIRM_MARKERS):
            return self._confirm_latest(db, context)
        return self._handle_detected_action(normalized, chat_repo, db, context)

    def _handle_detected_action(
        self,
        text: str,
        chat_repo: Any,
        db: Session,
        context: ChatActionContext,
    ) -> ChatActionResult | None:
        if self._contains(text, self.ADD_MARKERS):
            if not self._has_explicit_add_reference(text):
                return None
            return self._guarded_action("cart.add", lambda: self._add(text, chat_repo, db, context), db, context)
        if self._contains(text, self.REMOVE_MARKERS):
            payload = {"position": self._ordinal(text)}
            return self._guarded_action("cart.remove", lambda: self._remove(text, db, context), db, context, payload)
        if self._contains(text, self.CHECKOUT_MARKERS):
            return self._guarded_action("checkout.confirm", lambda: self._checkout(db, context), db, context)
        return None

    def _guarded_action(
        self,
        action: str,
        execute: Any,
        db: Session,
        context: ChatActionContext,
        payload: dict[str, Any] | None = None,
    ) -> ChatActionResult:
        if self._requires_auth(context):
            return self._auth_required(action, db, context)
        if self._requires_confirmation(action):
            return self._pending_confirmation(action, db, context, payload)
        result = execute()
        self._audit(db, context, action, "executed", result_payload=result.data)
        return result

    def _requires_auth(self, context: ChatActionContext) -> bool:
        if settings.app_env != "prod" or not settings.ai_chat_actions_require_auth_in_prod:
            return False
        return context.owner_auth_type != "user"

    def _requires_confirmation(self, action: str) -> bool:
        return (
            settings.app_env == "prod"
            and settings.ai_checkout_confirmation_required
            and action in {"cart.remove", "checkout.confirm"}
        )

    def _auth_required(self, action: str, db: Session, context: ChatActionContext) -> ChatActionResult:
        data = {"auth_required": True, "action_status": "auth_required"}
        self._audit(db, context, action, "auth_required", result_payload=data)
        return ChatActionResult(reply="这个操作需要先登录后再继续。", action=action, data=data)

    def _pending_confirmation(
        self,
        action: str,
        db: Session,
        context: ChatActionContext,
        resolved_payload: dict[str, Any] | None = None,
    ) -> ChatActionResult:
        action_id = uuid.uuid4().hex
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        payload = {
            "confirmation_id": action_id,
            "expires_at": expires_at.isoformat(),
            "action_status": "pending_confirmation",
        }
        self._audit(
            db,
            context,
            action,
            "pending_confirmation",
            action_id=action_id,
            resolved_payload=resolved_payload,
            result_payload=payload,
            expires_at=expires_at,
        )
        return ChatActionResult(reply="这个操作会修改购物车或生成订单，请回复“确认”后继续。", action=action, data=payload)

    def _confirm_latest(self, db: Session, context: ChatActionContext) -> ChatActionResult | None:
        action = self._latest_pending_action(db, context)
        if action is None:
            return None
        if action.expires_at and action.expires_at < datetime.utcnow():
            action.status = "expired"
            self._commit_audit(db)
            return ChatActionResult(reply="上一个确认请求已过期，请重新发起操作。", action=action.action, data={"action_status": "expired"})
        result = self._execute_confirmed(action, db, context)
        action.status = "executed"
        action.result_payload = result.data
        action.executed_at = datetime.utcnow()
        self._commit_audit(db)
        count_agent_action(action.action, "executed")
        return result

    def _execute_confirmed(self, action: AgentAction, db: Session, context: ChatActionContext) -> ChatActionResult:
        if action.action == "cart.remove":
            payload = action.resolved_payload if isinstance(action.resolved_payload, dict) else {}
            return self._remove_at_position(int(payload.get("position") or 1), db, context)
        if action.action == "checkout.confirm":
            return self._checkout(db, context)
        raise AppError("Unsupported pending action.", status_code=409, code="unsupported_pending_action")

    def _add(self, text: str, chat_repo: Any, db: Session, context: ChatActionContext) -> ChatActionResult:
        snapshot = self._latest_recommendation_snapshot(chat_repo, context.session_id)
        if snapshot is None:
            return ChatActionResult(reply="需要先完成一次导购推荐，我才能知道要把哪款加入购物车。", action="cart.add.needs_context")
        if self._requires_clearer_product_reference(text, snapshot):
            return ChatActionResult(reply="我没能确定要加哪款。可以说“把第一款加到购物车”。", action="cart.add.needs_reference")
        product_refs = self._resolve_product_refs(text, snapshot)
        if not product_refs:
            return ChatActionResult(reply="我没能确定要加哪款。可以说“把第一款加到购物车”。", action="cart.add.needs_reference")
        return self._add_products(text, product_refs, db, context)

    def _add_products(self, text: str, product_refs: list[dict[str, Any]], db: Session, context: ChatActionContext) -> ChatActionResult:
        cart = None
        for product_ref in product_refs:
            cart = CartService(db).create_item(
                CartItemCreate(
                    product_id=int(product_ref["id"]),
                    quantity=self._quantity(text),
                    source_session_id=context.session_id,
                    source_label=product_ref.get("name"),
                ),
                context.user_ref,
            )
        names = "、".join(str(product.get("name") or f"商品{product['id']}") for product in product_refs[:3])
        reply = f"已加入购物车：{names}。" if len(product_refs) == 1 else f"已把这套方案的 {len(product_refs)} 件商品加入购物车。"
        return ChatActionResult(reply=reply, action="cart.add", data={"cart": self._dump(cart), "product_ids": [item["id"] for item in product_refs]})

    def _remove(self, text: str, db: Session, context: ChatActionContext) -> ChatActionResult:
        return self._remove_at_position(self._ordinal(text), db, context)

    def _remove_at_position(self, position: int, db: Session, context: ChatActionContext) -> ChatActionResult:
        cart, removed_name = CartService(db).delete_item_at_position(position, context.user_ref)
        return ChatActionResult(
            reply=f"已从购物车删除第 {position} 项：{removed_name}。",
            action="cart.remove",
            data={"cart": self._dump(cart), "position": position},
        )

    def _checkout(self, db: Session, context: ChatActionContext) -> ChatActionResult:
        try:
            checkout = CartService(db).create_checkout(CheckoutCreate(use_default_address=True, source_session_id=context.session_id), context.user_ref)
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

    def _audit(
        self,
        db: Session,
        context: ChatActionContext,
        action: str,
        status: str,
        *,
        action_id: str | None = None,
        resolved_payload: dict[str, Any] | None = None,
        result_payload: dict[str, Any] | None = None,
        expires_at: datetime | None = None,
    ) -> None:
        AgentActionRepository(db).create_action(
            AgentAction(
                action_id=action_id or uuid.uuid4().hex,
                session_id=context.session_id,
                owner_subject=context.owner_subject,
                owner_auth_type=context.owner_auth_type,
                action=action,
                status=status,
                confirmation_required=status == "pending_confirmation",
                resolved_payload=resolved_payload,
                result_payload=result_payload,
                request_id=None,
                expires_at=expires_at,
                created_at=datetime.utcnow(),
            )
        )
        self._commit_audit(db)
        count_agent_action(action, status)

    def _latest_pending_action(self, db: Session, context: ChatActionContext) -> AgentAction | None:
        from sqlalchemy import select

        statement = (
            select(AgentAction)
            .where(
                AgentAction.session_id == context.session_id,
                AgentAction.owner_subject == context.owner_subject,
                AgentAction.status == "pending_confirmation",
            )
            .order_by(AgentAction.created_at.desc(), AgentAction.id.desc())
            .limit(1)
        )
        return db.scalar(statement)

    def _commit_audit(self, db: Session) -> None:
        db.commit()

    def _resolve_product_refs(self, text: str, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        if self._contains(text, self.PLAN_MARKERS) and snapshot.get("bundle_plans"):
            return self._product_refs_from_plan(text, snapshot)
        products = snapshot.get("products") or self._products_from_bundle(snapshot)
        if not products:
            return []
        index = self._ordinal(text) - 1
        if index < 0 or index >= len(products):
            return []
        product = products[index]
        return [product] if isinstance(product, dict) and product.get("id") is not None else []

    def _product_refs_from_plan(self, text: str, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        plan = self._plan_at(snapshot.get("bundle_plans") or [], self._ordinal(text))
        if plan is None:
            return []
        return [
            product
            for item in plan.get("items", [])
            if isinstance(item, dict)
            for product in [item.get("product")]
            if isinstance(product, dict) and product.get("id") is not None
        ]

    def _latest_recommendation_snapshot(self, chat_repo: Any, session_id: str) -> dict[str, Any] | None:
        for message in reversed(chat_repo.list_messages(session_id, limit=20)):
            structured_data = getattr(message, "structured_data", None) or {}
            if structured_data.get("products") or structured_data.get("bundle_plans"):
                return structured_data
        return None

    def _requires_clearer_product_reference(self, text: str, snapshot: dict[str, Any]) -> bool:
        if self._has_explicit_plan_reference(text):
            return False
        products = snapshot.get("products") or self._products_from_bundle(snapshot)
        if len(products) <= 1:
            return False
        weak_markers = ["这款", "这件", "这个", "这一个", "它"]
        if not self._contains(text, weak_markers):
            return False
        return not self._has_ordinal_reference(text)

    def _products_from_bundle(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        products = []
        for plan in snapshot.get("bundle_plans") or []:
            for item in plan.get("items", []):
                product = item.get("product") if isinstance(item, dict) else None
                if isinstance(product, dict):
                    products.append(product)
        return products

    def _plan_at(self, plans: list[Any], ordinal: int) -> dict[str, Any] | None:
        index = min(max(ordinal - 1, 0), max(len(plans) - 1, 0))
        plan = plans[index] if plans else None
        return plan if isinstance(plan, dict) else None

    def _ordinal(self, text: str) -> int:
        for marker, value in self.ORDINALS.items():
            if marker in text:
                return value
        match = re.search(r"第?\s*(\d+)\s*(?:个|款|项|件|套)?", text)
        return int(match.group(1)) if match else 1

    def _has_explicit_add_reference(self, text: str) -> bool:
        return self._has_explicit_product_reference(text) or self._has_explicit_plan_reference(text)

    def _has_explicit_product_reference(self, text: str) -> bool:
        if self._contains(text, self.EXPLICIT_PRODUCT_REFERENCE_MARKERS):
            return True
        return self._has_ordinal_reference(text)

    def _has_explicit_plan_reference(self, text: str) -> bool:
        if self._contains(text, self.EXPLICIT_PLAN_REFERENCE_MARKERS):
            return True
        return bool(re.search(r"第\s*\d+\s*套", text))

    def _has_ordinal_reference(self, text: str) -> bool:
        return bool(re.search(r"第\s*\d+\s*(?:个|款|项|件)?", text))

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
