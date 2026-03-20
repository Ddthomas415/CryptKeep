from __future__ import annotations

from enum import StrEnum

from domain.state_machines.common import TransitionResult, allow_transition, deny_transition


class KillSwitchState(StrEnum):
    OFF = "off"
    ARMING = "arming"
    ON = "on"
    RELEASING = "releasing"


_KILL_SWITCH_TRANSITIONS: dict[KillSwitchState, set[KillSwitchState]] = {
    KillSwitchState.OFF: {KillSwitchState.ARMING},
    KillSwitchState.ARMING: {KillSwitchState.ON},
    KillSwitchState.ON: {KillSwitchState.RELEASING},
    KillSwitchState.RELEASING: {KillSwitchState.OFF, KillSwitchState.ON},
}


def can_transition_kill_switch(
    *,
    from_state: KillSwitchState,
    to_state: KillSwitchState,
    actor_authorized: bool = True,
    pause_applied: bool = True,
    submission_blocked: bool = True,
    release_validated: bool = True,
) -> TransitionResult[KillSwitchState]:
    if from_state == to_state:
        return allow_transition(from_state=from_state, to_state=to_state, reason="NO_OP")
    if to_state not in _KILL_SWITCH_TRANSITIONS.get(from_state, set()):
        return deny_transition(from_state=from_state, to_state=to_state, reason="TRANSITION_NOT_ALLOWED")
    if not actor_authorized:
        return deny_transition(from_state=from_state, to_state=to_state, reason="ROLE_NOT_ALLOWED")

    if from_state == KillSwitchState.ARMING and to_state == KillSwitchState.ON:
        if not pause_applied or not submission_blocked:
            return deny_transition(from_state=from_state, to_state=to_state, reason="ARMING_INCOMPLETE")

    if from_state == KillSwitchState.RELEASING and to_state == KillSwitchState.OFF and not release_validated:
        return deny_transition(from_state=from_state, to_state=to_state, reason="RELEASE_VALIDATION_FAILED")

    return allow_transition(from_state=from_state, to_state=to_state, reason="ALLOWED")
