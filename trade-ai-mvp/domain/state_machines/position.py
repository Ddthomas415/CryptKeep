from __future__ import annotations

from enum import StrEnum

from domain.state_machines.common import TransitionResult, allow_transition, deny_transition


class PositionState(StrEnum):
    OPENING = "opening"
    OPEN = "open"
    REDUCING = "reducing"
    CLOSING = "closing"
    CLOSED = "closed"
    LIQUIDATED = "liquidated"
    ERROR_STATE = "error_state"


_POSITION_TRANSITIONS: dict[PositionState, set[PositionState]] = {
    PositionState.OPENING: {PositionState.OPEN, PositionState.CLOSING, PositionState.ERROR_STATE},
    PositionState.OPEN: {PositionState.REDUCING, PositionState.CLOSING, PositionState.LIQUIDATED, PositionState.ERROR_STATE},
    PositionState.REDUCING: {PositionState.OPEN, PositionState.CLOSING, PositionState.ERROR_STATE},
    PositionState.CLOSING: {PositionState.CLOSED, PositionState.ERROR_STATE},
    PositionState.CLOSED: set(),
    PositionState.LIQUIDATED: set(),
    PositionState.ERROR_STATE: set(),
}


def can_transition_position(
    *,
    from_state: PositionState,
    to_state: PositionState,
    has_fill: bool = True,
    net_size_zero: bool = False,
    reconciliation_issue: bool = False,
) -> TransitionResult[PositionState]:
    if from_state == to_state:
        return allow_transition(from_state=from_state, to_state=to_state, reason="NO_OP")
    if to_state not in _POSITION_TRANSITIONS.get(from_state, set()):
        return deny_transition(from_state=from_state, to_state=to_state, reason="TRANSITION_NOT_ALLOWED")

    if to_state == PositionState.ERROR_STATE:
        if not reconciliation_issue:
            return deny_transition(from_state=from_state, to_state=to_state, reason="ERROR_STATE_REQUIRES_RECONCILIATION_ISSUE")
        return allow_transition(
            from_state=from_state,
            to_state=to_state,
            reason="RECONCILIATION_REQUIRED",
            side_effects=["trigger_position_reconciliation"],
        )

    if from_state == PositionState.OPENING and to_state == PositionState.OPEN and not has_fill:
        return deny_transition(from_state=from_state, to_state=to_state, reason="MISSING_FILL")

    if from_state == PositionState.CLOSING and to_state == PositionState.CLOSED and not net_size_zero:
        return deny_transition(from_state=from_state, to_state=to_state, reason="POSITION_NOT_FLAT")

    return allow_transition(from_state=from_state, to_state=to_state, reason="ALLOWED")
