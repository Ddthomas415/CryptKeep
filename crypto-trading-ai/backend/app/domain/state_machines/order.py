from __future__ import annotations

from enum import Enum

from backend.app.domain.state_machines.common import TransitionResult, allow_transition, block_transition


class OrderState(str, Enum):
    CREATED = "created"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCEL_REQUESTED = "cancel_requested"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    FAILED = "failed"
    EXPIRED = "expired"


ALLOWED_ORDER_TRANSITIONS: set[tuple[OrderState, OrderState]] = {
    (OrderState.CREATED, OrderState.SUBMITTED),
    (OrderState.SUBMITTED, OrderState.ACKNOWLEDGED),
    (OrderState.SUBMITTED, OrderState.REJECTED),
    (OrderState.SUBMITTED, OrderState.FAILED),
    (OrderState.ACKNOWLEDGED, OrderState.PARTIALLY_FILLED),
    (OrderState.ACKNOWLEDGED, OrderState.FILLED),
    (OrderState.ACKNOWLEDGED, OrderState.CANCEL_REQUESTED),
    (OrderState.PARTIALLY_FILLED, OrderState.FILLED),
    (OrderState.PARTIALLY_FILLED, OrderState.CANCEL_REQUESTED),
    (OrderState.CANCEL_REQUESTED, OrderState.CANCELLED),
    (OrderState.CANCEL_REQUESTED, OrderState.PARTIALLY_FILLED),
    (OrderState.CANCEL_REQUESTED, OrderState.FILLED),
}


def can_transition_order(
    from_state: OrderState,
    to_state: OrderState,
    *,
    context: dict | None = None,
) -> TransitionResult:
    if from_state == to_state:
        return allow_transition(from_state.value, to_state.value, reason="no_op")

    ctx = context or {}
    if to_state in {OrderState.REJECTED, OrderState.FAILED, OrderState.EXPIRED}:
        if to_state == OrderState.REJECTED and ctx.get("actor_type") != "exchange":
            return block_transition(from_state.value, to_state.value, "REJECTED_REQUIRES_EXCHANGE_ACTOR")
        if to_state == OrderState.FAILED and ctx.get("actor_type") == "exchange":
            return block_transition(from_state.value, to_state.value, "FAILED_REQUIRES_SYSTEM_ACTOR")
        return allow_transition(from_state.value, to_state.value)

    if (from_state, to_state) not in ALLOWED_ORDER_TRANSITIONS:
        return block_transition(from_state.value, to_state.value, "ORDER_TRANSITION_NOT_ALLOWED")

    if to_state == OrderState.SUBMITTED and not ctx.get("execution_allowed", False):
        return block_transition(from_state.value, to_state.value, "EXECUTION_BLOCKED")
    if to_state == OrderState.ACKNOWLEDGED and not ctx.get("exchange_ack", False):
        return block_transition(from_state.value, to_state.value, "MISSING_EXCHANGE_ACK")
    if to_state == OrderState.CANCEL_REQUESTED and not ctx.get("cancellable", True):
        return block_transition(from_state.value, to_state.value, "ORDER_NOT_CANCELLABLE")
    if to_state == OrderState.CANCELLED and not ctx.get("cancel_confirmed", True):
        return block_transition(from_state.value, to_state.value, "CANCEL_NOT_CONFIRMED")

    side_effects: tuple[str, ...] = ()
    if to_state in {OrderState.PARTIALLY_FILLED, OrderState.FILLED}:
        side_effects = ("publish_fill_event", "update_position_snapshot")
    elif to_state == OrderState.CANCEL_REQUESTED:
        side_effects = ("dispatch_cancel_to_exchange",)

    return allow_transition(from_state.value, to_state.value, side_effects=side_effects)
