from __future__ import annotations

from enum import StrEnum

from domain.state_machines.common import TransitionResult, allow_transition, deny_transition


class ApprovalState(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


_APPROVAL_TRANSITIONS: dict[ApprovalState, set[ApprovalState]] = {
    ApprovalState.PENDING: {
        ApprovalState.APPROVED,
        ApprovalState.REJECTED,
        ApprovalState.EXPIRED,
        ApprovalState.CANCELLED,
    },
    ApprovalState.APPROVED: {ApprovalState.CANCELLED},
    ApprovalState.REJECTED: set(),
    ApprovalState.EXPIRED: set(),
    ApprovalState.CANCELLED: set(),
}


def can_transition_approval(
    *,
    from_state: ApprovalState,
    to_state: ApprovalState,
    actor_authorized: bool = True,
    recommendation_valid: bool = True,
    risk_passed: bool = True,
    kill_switch: bool = False,
    approval_window_open: bool = True,
    exchange_healthy: bool = True,
) -> TransitionResult[ApprovalState]:
    if from_state == to_state:
        return allow_transition(from_state=from_state, to_state=to_state, reason="NO_OP")
    if to_state not in _APPROVAL_TRANSITIONS.get(from_state, set()):
        return deny_transition(from_state=from_state, to_state=to_state, reason="TRANSITION_NOT_ALLOWED")

    if from_state == ApprovalState.PENDING and to_state == ApprovalState.APPROVED:
        if not actor_authorized:
            return deny_transition(from_state=from_state, to_state=to_state, reason="ROLE_NOT_ALLOWED")
        if not approval_window_open:
            return deny_transition(from_state=from_state, to_state=to_state, reason="APPROVAL_EXPIRED")
        if not recommendation_valid:
            return deny_transition(from_state=from_state, to_state=to_state, reason="RECOMMENDATION_INVALID")
        if kill_switch:
            return deny_transition(from_state=from_state, to_state=to_state, reason="KILL_SWITCH_ACTIVE")
        if not risk_passed:
            return deny_transition(from_state=from_state, to_state=to_state, reason="RISK_BLOCKED")
        if not exchange_healthy:
            return deny_transition(from_state=from_state, to_state=to_state, reason="CONNECTION_UNHEALTHY")

    if to_state == ApprovalState.EXPIRED and approval_window_open:
        return deny_transition(from_state=from_state, to_state=to_state, reason="APPROVAL_WINDOW_STILL_OPEN")

    return allow_transition(from_state=from_state, to_state=to_state, reason="ALLOWED")
