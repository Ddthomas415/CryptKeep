from __future__ import annotations

from enum import StrEnum

from domain.state_machines.common import TransitionResult, allow_transition, deny_transition


class SafetyState(StrEnum):
    SAFE = "safe"
    WARNING = "warning"
    RESTRICTED = "restricted"
    PAUSED = "paused"
    BLOCKED = "blocked"


_SAFETY_TRANSITIONS: dict[SafetyState, set[SafetyState]] = {
    SafetyState.SAFE: {SafetyState.WARNING, SafetyState.BLOCKED},
    SafetyState.WARNING: {SafetyState.SAFE, SafetyState.RESTRICTED, SafetyState.BLOCKED},
    SafetyState.RESTRICTED: {SafetyState.WARNING, SafetyState.PAUSED, SafetyState.BLOCKED},
    SafetyState.PAUSED: {SafetyState.RESTRICTED, SafetyState.BLOCKED, SafetyState.SAFE},
    SafetyState.BLOCKED: {SafetyState.PAUSED, SafetyState.RESTRICTED, SafetyState.WARNING, SafetyState.SAFE},
}


def can_transition_safety(
    *,
    from_state: SafetyState,
    to_state: SafetyState,
    kill_switch_on: bool = False,
    severe_incident: bool = False,
    release_validated: bool = True,
) -> TransitionResult[SafetyState]:
    if from_state == to_state:
        return allow_transition(from_state=from_state, to_state=to_state, reason="NO_OP")
    if to_state not in _SAFETY_TRANSITIONS.get(from_state, set()):
        return deny_transition(from_state=from_state, to_state=to_state, reason="TRANSITION_NOT_ALLOWED")

    if kill_switch_on and to_state != SafetyState.BLOCKED:
        return deny_transition(from_state=from_state, to_state=to_state, reason="KILL_SWITCH_FORCES_BLOCKED")

    if severe_incident and to_state not in {SafetyState.PAUSED, SafetyState.BLOCKED}:
        return deny_transition(from_state=from_state, to_state=to_state, reason="SEVERE_INCIDENT_REQUIRES_ESCALATION")

    if from_state == SafetyState.BLOCKED and to_state in {SafetyState.WARNING, SafetyState.SAFE} and not release_validated:
        return deny_transition(from_state=from_state, to_state=to_state, reason="RELEASE_VALIDATION_FAILED")

    return allow_transition(from_state=from_state, to_state=to_state, reason="ALLOWED")
