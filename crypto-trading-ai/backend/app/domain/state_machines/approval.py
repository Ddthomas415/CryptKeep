from __future__ import annotations

from enum import Enum

from backend.app.domain.state_machines.common import TransitionResult, allow_transition, block_transition


class ApprovalState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


ALLOWED_APPROVAL_TRANSITIONS: set[tuple[ApprovalState, ApprovalState]] = {
    (ApprovalState.PENDING, ApprovalState.APPROVED),
    (ApprovalState.PENDING, ApprovalState.REJECTED),
    (ApprovalState.PENDING, ApprovalState.EXPIRED),
    (ApprovalState.PENDING, ApprovalState.CANCELLED),
    (ApprovalState.APPROVED, ApprovalState.CANCELLED),
}


def can_transition_approval(
    from_state: ApprovalState,
    to_state: ApprovalState,
    *,
    context: dict | None = None,
) -> TransitionResult:
    if from_state == to_state:
        return allow_transition(from_state.value, to_state.value, reason="no_op")

    if (from_state, to_state) not in ALLOWED_APPROVAL_TRANSITIONS:
        return block_transition(from_state.value, to_state.value, "APPROVAL_TRANSITION_NOT_ALLOWED")

    ctx = context or {}
    if to_state == ApprovalState.APPROVED and not ctx.get("approver_allowed", False):
        return block_transition(from_state.value, to_state.value, "ROLE_NOT_ALLOWED")
    if to_state == ApprovalState.EXPIRED and not ctx.get("expired", True):
        return block_transition(from_state.value, to_state.value, "APPROVAL_NOT_EXPIRED")

    return allow_transition(from_state.value, to_state.value)
