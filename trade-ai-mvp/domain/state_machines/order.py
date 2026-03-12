from __future__ import annotations

from enum import StrEnum

from domain.state_machines.common import TransitionResult, allow_transition, deny_transition
from shared.schemas.api import Mode


class OrderState(StrEnum):
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


_ORDER_TRANSITIONS: dict[OrderState, set[OrderState]] = {
    OrderState.CREATED: {OrderState.SUBMITTED},
    OrderState.SUBMITTED: {OrderState.ACKNOWLEDGED, OrderState.REJECTED, OrderState.FAILED},
    OrderState.ACKNOWLEDGED: {OrderState.PARTIALLY_FILLED, OrderState.FILLED, OrderState.CANCEL_REQUESTED, OrderState.EXPIRED},
    OrderState.PARTIALLY_FILLED: {OrderState.FILLED, OrderState.CANCEL_REQUESTED},
    OrderState.CANCEL_REQUESTED: {OrderState.CANCELLED, OrderState.PARTIALLY_FILLED, OrderState.FILLED},
    OrderState.FILLED: set(),
    OrderState.CANCELLED: set(),
    OrderState.REJECTED: set(),
    OrderState.FAILED: set(),
    OrderState.EXPIRED: set(),
}


def can_transition_order(
    *,
    from_state: OrderState,
    to_state: OrderState,
    mode: Mode,
    approval_ready: bool = True,
    risk_passed: bool = True,
    exchange_healthy: bool = True,
    kill_switch: bool = False,
) -> TransitionResult[OrderState]:
    if from_state == to_state:
        return allow_transition(from_state=from_state, to_state=to_state, reason="NO_OP")
    if to_state not in _ORDER_TRANSITIONS.get(from_state, set()):
        return deny_transition(from_state=from_state, to_state=to_state, reason="TRANSITION_NOT_ALLOWED")

    if from_state == OrderState.CREATED and to_state == OrderState.SUBMITTED:
        if mode == Mode.RESEARCH_ONLY:
            return deny_transition(from_state=from_state, to_state=to_state, reason="MODE_BLOCKED")
        if kill_switch:
            return deny_transition(from_state=from_state, to_state=to_state, reason="KILL_SWITCH_ACTIVE")
        if not approval_ready:
            return deny_transition(from_state=from_state, to_state=to_state, reason="APPROVAL_REQUIRED")
        if not risk_passed:
            return deny_transition(from_state=from_state, to_state=to_state, reason="RISK_BLOCKED")
        if not exchange_healthy:
            return deny_transition(from_state=from_state, to_state=to_state, reason="CONNECTION_UNHEALTHY")

    # The state machine explicitly separates `rejected` and `failed`.
    if from_state == OrderState.SUBMITTED and to_state == OrderState.REJECTED:
        return allow_transition(from_state=from_state, to_state=to_state, reason="EXCHANGE_OR_POLICY_REJECTION")
    if from_state == OrderState.SUBMITTED and to_state == OrderState.FAILED:
        return allow_transition(from_state=from_state, to_state=to_state, reason="TRANSPORT_OR_SYNC_FAILURE")

    return allow_transition(from_state=from_state, to_state=to_state, reason="ALLOWED")
