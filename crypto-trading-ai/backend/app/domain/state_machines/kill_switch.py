from __future__ import annotations

from enum import Enum

from backend.app.domain.state_machines.common import TransitionResult, allow_transition, block_transition


class KillSwitchState(str, Enum):
    OFF = "off"
    ARMING = "arming"
    ON = "on"
    RELEASING = "releasing"


ALLOWED_KILL_SWITCH_TRANSITIONS: set[tuple[KillSwitchState, KillSwitchState]] = {
    (KillSwitchState.OFF, KillSwitchState.ARMING),
    (KillSwitchState.ARMING, KillSwitchState.ON),
    (KillSwitchState.ON, KillSwitchState.RELEASING),
    (KillSwitchState.RELEASING, KillSwitchState.OFF),
    (KillSwitchState.RELEASING, KillSwitchState.ON),
}


def can_transition_kill_switch(
    from_state: KillSwitchState,
    to_state: KillSwitchState,
    *,
    context: dict | None = None,
) -> TransitionResult:
    if from_state == to_state:
        return allow_transition(from_state.value, to_state.value, reason="no_op")

    if (from_state, to_state) not in ALLOWED_KILL_SWITCH_TRANSITIONS:
        return block_transition(from_state.value, to_state.value, "KILL_SWITCH_TRANSITION_NOT_ALLOWED")

    ctx = context or {}
    if from_state == KillSwitchState.OFF and to_state == KillSwitchState.ARMING:
        if not (ctx.get("authorized_user", False) or ctx.get("auto_trigger", False)):
            return block_transition(from_state.value, to_state.value, "NOT_AUTHORIZED")
    if from_state == KillSwitchState.ARMING and to_state == KillSwitchState.ON:
        if not ctx.get("arming_complete", False):
            return block_transition(from_state.value, to_state.value, "ARMING_NOT_COMPLETE")
    if from_state == KillSwitchState.ON and to_state == KillSwitchState.RELEASING:
        if not ctx.get("authorized_user", False):
            return block_transition(from_state.value, to_state.value, "NOT_AUTHORIZED")
        if not ctx.get("reason_provided", False):
            return block_transition(from_state.value, to_state.value, "REASON_REQUIRED")
    if from_state == KillSwitchState.RELEASING and to_state == KillSwitchState.OFF:
        if not ctx.get("release_checks_passed", False):
            return block_transition(from_state.value, to_state.value, "RELEASE_VALIDATION_FAILED")
    if from_state == KillSwitchState.RELEASING and to_state == KillSwitchState.ON:
        if ctx.get("release_checks_passed", False):
            return block_transition(from_state.value, to_state.value, "RELEASE_VALIDATION_PASSED")

    side_effects: tuple[str, ...] = ()
    if to_state == KillSwitchState.ON:
        side_effects = ("block_new_orders", "pause_strategies", "cancel_pending_orders")
    elif to_state == KillSwitchState.OFF:
        side_effects = ("re_enable_submission_paths",)

    return allow_transition(from_state.value, to_state.value, side_effects=side_effects)
