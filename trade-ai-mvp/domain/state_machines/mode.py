from __future__ import annotations

from enum import StrEnum

from domain.state_machines.common import TransitionResult, allow_transition, deny_transition


class ModeState(StrEnum):
    RESEARCH_ONLY = "research_only"
    PAPER = "paper"
    LIVE_APPROVAL = "live_approval"
    LIVE_AUTO = "live_auto"


_MODE_TRANSITIONS: dict[ModeState, set[ModeState]] = {
    ModeState.RESEARCH_ONLY: {ModeState.PAPER, ModeState.LIVE_APPROVAL},
    ModeState.PAPER: {ModeState.RESEARCH_ONLY, ModeState.LIVE_APPROVAL},
    ModeState.LIVE_APPROVAL: {ModeState.RESEARCH_ONLY, ModeState.PAPER, ModeState.LIVE_AUTO},
    ModeState.LIVE_AUTO: {ModeState.RESEARCH_ONLY, ModeState.PAPER, ModeState.LIVE_APPROVAL},
}


def can_transition_mode(
    *,
    from_state: ModeState,
    to_state: ModeState,
    has_trading_connection: bool = False,
    risk_limits_configured: bool = False,
    user_confirmed: bool = False,
    second_confirmation: bool = False,
    kill_switch_available: bool = True,
) -> TransitionResult[ModeState]:
    if from_state == to_state:
        return allow_transition(from_state=from_state, to_state=to_state, reason="NO_OP")
    if to_state not in _MODE_TRANSITIONS.get(from_state, set()):
        return deny_transition(from_state=from_state, to_state=to_state, reason="TRANSITION_NOT_ALLOWED")

    if to_state in {ModeState.LIVE_APPROVAL, ModeState.LIVE_AUTO}:
        if not has_trading_connection:
            return deny_transition(from_state=from_state, to_state=to_state, reason="MISSING_TRADING_CONNECTION")
        if not risk_limits_configured:
            return deny_transition(from_state=from_state, to_state=to_state, reason="RISK_LIMITS_NOT_CONFIGURED")
        if not user_confirmed:
            return deny_transition(from_state=from_state, to_state=to_state, reason="USER_CONFIRMATION_REQUIRED")

    if to_state == ModeState.LIVE_AUTO:
        if not second_confirmation:
            return deny_transition(from_state=from_state, to_state=to_state, reason="SECOND_CONFIRMATION_REQUIRED")
        if not kill_switch_available:
            return deny_transition(from_state=from_state, to_state=to_state, reason="KILL_SWITCH_UNAVAILABLE")

    return allow_transition(from_state=from_state, to_state=to_state, reason="ALLOWED")
