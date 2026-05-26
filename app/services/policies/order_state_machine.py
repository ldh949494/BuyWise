"""Order fulfillment state machine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


class PaymentStatus:
    PAID = "paid"
    CANCELLED = "cancelled"


class FulfillmentStatus:
    PENDING = "pending"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class InitialOrderState:
    payment_status: str
    fulfillment_status: str
    delivered_at: datetime | None
    feedback_due_at: datetime | None


@dataclass(frozen=True)
class OrderTransition:
    fulfillment_status: str | None = None
    shipped_at: datetime | None = None
    delivered_at: datetime | None = None
    item_feedback_due_at: datetime | None = None
    no_op: bool = False
    valid: bool = True


class OrderStateMachine:
    def __init__(self, *, feedback_delay_days: int) -> None:
        self.feedback_delay_days = feedback_delay_days

    def build_initial_order_state(
        self,
        *,
        external_purchase: bool,
        external_feedback_mode: str,
        now: datetime,
    ) -> InitialOrderState:
        feedback_due_at = self._initial_feedback_due_at(external_purchase, external_feedback_mode, now)
        return InitialOrderState(
            payment_status=PaymentStatus.PAID,
            fulfillment_status=self._initial_fulfillment_status(feedback_due_at),
            delivered_at=now if feedback_due_at is not None else None,
            feedback_due_at=feedback_due_at,
        )

    def build_transition(self, fulfillment_status: str, *, now: datetime) -> OrderTransition:
        if fulfillment_status == FulfillmentStatus.PENDING:
            return OrderTransition(
                fulfillment_status=FulfillmentStatus.SHIPPED,
                shipped_at=now,
            )
        if fulfillment_status == FulfillmentStatus.SHIPPED:
            return OrderTransition(
                fulfillment_status=FulfillmentStatus.DELIVERED,
                delivered_at=now,
                item_feedback_due_at=now + timedelta(days=self.feedback_delay_days),
            )
        if fulfillment_status == FulfillmentStatus.DELIVERED:
            return OrderTransition(no_op=True)
        return OrderTransition(valid=False)

    def _initial_fulfillment_status(self, feedback_due_at: datetime | None) -> str:
        if feedback_due_at is not None:
            return FulfillmentStatus.DELIVERED
        return FulfillmentStatus.PENDING

    def _initial_feedback_due_at(
        self,
        external_purchase: bool,
        external_feedback_mode: str,
        now: datetime,
    ) -> datetime | None:
        if not external_purchase:
            return None
        if external_feedback_mode == "immediate":
            return now
        return now + timedelta(days=self.feedback_delay_days)
