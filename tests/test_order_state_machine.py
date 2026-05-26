from datetime import datetime, timedelta

from app.services.policies.order_state_machine import FulfillmentStatus, OrderStateMachine, PaymentStatus


NOW = datetime(2026, 1, 15, 12, 0, 0)


def test_initial_state_for_internal_order_is_pending() -> None:
    machine = OrderStateMachine(feedback_delay_days=3)

    initial = machine.build_initial_order_state(external_purchase=False, external_feedback_mode="delayed", now=NOW)

    assert initial.payment_status == PaymentStatus.PAID
    assert initial.fulfillment_status == FulfillmentStatus.PENDING
    assert initial.delivered_at is None
    assert initial.feedback_due_at is None


def test_initial_state_for_external_order_is_delivered_with_due_at() -> None:
    machine = OrderStateMachine(feedback_delay_days=3)

    immediate = machine.build_initial_order_state(external_purchase=True, external_feedback_mode="immediate", now=NOW)
    delayed = machine.build_initial_order_state(external_purchase=True, external_feedback_mode="delayed", now=NOW)

    assert immediate.fulfillment_status == FulfillmentStatus.DELIVERED
    assert immediate.delivered_at == NOW
    assert immediate.feedback_due_at == NOW
    assert delayed.feedback_due_at == NOW + timedelta(days=3)


def test_advance_pending_to_shipped() -> None:
    machine = OrderStateMachine(feedback_delay_days=3)

    transition = machine.build_transition(FulfillmentStatus.PENDING, now=NOW)

    assert transition.fulfillment_status == FulfillmentStatus.SHIPPED
    assert transition.shipped_at == NOW
    assert transition.delivered_at is None
    assert transition.item_feedback_due_at is None
    assert transition.no_op is False
    assert transition.valid is True


def test_advance_shipped_to_delivered_sets_feedback_due_at() -> None:
    machine = OrderStateMachine(feedback_delay_days=3)

    transition = machine.build_transition(FulfillmentStatus.SHIPPED, now=NOW)

    assert transition.fulfillment_status == FulfillmentStatus.DELIVERED
    assert transition.shipped_at is None
    assert transition.delivered_at == NOW
    assert transition.item_feedback_due_at == NOW + timedelta(days=3)
    assert transition.no_op is False
    assert transition.valid is True


def test_advance_delivered_is_no_op_and_cancelled_is_invalid() -> None:
    machine = OrderStateMachine(feedback_delay_days=3)

    no_op = machine.build_transition(FulfillmentStatus.DELIVERED, now=NOW)
    invalid = machine.build_transition(FulfillmentStatus.CANCELLED, now=NOW)
    unknown = machine.build_transition("unknown", now=NOW)

    assert no_op.no_op is True
    assert no_op.valid is True
    assert invalid.valid is False
    assert unknown.valid is False
