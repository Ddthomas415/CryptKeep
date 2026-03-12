from __future__ import annotations

from enum import Enum

from backend.app.domain.state_machines.common import TransitionResult, allow_transition, block_transition


class PositionState(str, Enum):
    OPENING = "opening"
    OPEN = "open"
    REDUCING = "reducing"
    CLOSING = "closing"
    CLOSED = "closed"
    LIQUIDATED = "liquidated"
    ERROR_STATE = "error_state"


ALLOWED_POSITION_TRANSITIONS: set[tuple[PositionState, PositionState]] = {
    (PositionState.OPENING, PositionState.OPEN),
    (PositionState.OPENING, PositionState.CLOSING),
    (PositionState.OPENING, PositionState.ERROR_STATE),
    (PositionState.OPEN, PositionState.REDUCING),
    (PositionState.OPEN, PositionState.CLOSING),
    (PositionState.OPEN, PositionState.LIQUIDATED),
    (PositionState.OPEN, PositionState.ERROR_STATE),
    (PositionState.REDUCING, PositionState.OPEN),
    (PositionState.REDUCING, PositionState.CLOSING),
    (PositionState.REDUCING, PositionState.ERROR_STATE),
    (PositionState.CLOSING, PositionState.CLOSED),
    (PositionState.CLOSING, PositionState.ERROR_STATE),
}


def can_transition_position(
    from_state: PositionState,
    to_state: PositionState,
    *,
    context: dict | None = None,
) -> TransitionResult:
    if from_state == to_state:
        return allow_transition(from_state.value, to_state.value, reason="no_op")

    if (from_state, to_state) not in ALLOWED_POSITION_TRANSITIONS:
        return block_transition(from_state.value, to_state.value, "POSITION_TRANSITION_NOT_ALLOWED")

    ctx = context or {}
    if from_state == PositionState.OPENING and to_state == PositionState.OPEN:
        if not ctx.get("exposure_positive", False):
            return block_transition(from_state.value, to_state.value, "EXPOSURE_NOT_ESTABLISHED")
    if from_state == PositionState.OPEN and to_state == PositionState.REDUCING:
        if not ctx.get("partial_exit_initiated", False):
            return block_transition(from_state.value, to_state.value, "PARTIAL_EXIT_NOT_INITIATED")
    if from_state == PositionState.OPEN and to_state == PositionState.CLOSING:
        if not (ctx.get("full_close_initiated", False) or ctx.get("risk_forced_close", False)):
            return block_transition(from_state.value, to_state.value, "FULL_CLOSE_NOT_INITIATED")
    if from_state == PositionState.CLOSING and to_state == PositionState.CLOSED:
        if not ctx.get("net_size_zero", False):
            return block_transition(from_state.value, to_state.value, "POSITION_EXPOSURE_NOT_ZERO")
    if to_state == PositionState.ERROR_STATE and not ctx.get("reconciliation_issue", True):
        return block_transition(from_state.value, to_state.value, "NO_RECONCILIATION_ISSUE")

    return allow_transition(from_state.value, to_state.value)
