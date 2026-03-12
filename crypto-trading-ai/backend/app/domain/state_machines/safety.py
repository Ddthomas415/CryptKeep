from __future__ import annotations

from enum import Enum

from backend.app.domain.state_machines.common import TransitionResult, allow_transition, block_transition


class SafetyState(str, Enum):
    SAFE = "safe"
    WARNING = "warning"
    RESTRICTED = "restricted"
    PAUSED = "paused"
    BLOCKED = "blocked"


_SEVERITY: dict[SafetyState, int] = {
    SafetyState.SAFE: 0,
    SafetyState.WARNING: 1,
    SafetyState.RESTRICTED: 2,
    SafetyState.PAUSED: 3,
    SafetyState.BLOCKED: 4,
}


def can_transition_safety(
    from_state: SafetyState,
    to_state: SafetyState,
    *,
    context: dict | None = None,
) -> TransitionResult:
    if from_state == to_state:
        return allow_transition(from_state.value, to_state.value, reason="no_op")

    ctx = context or {}
    if to_state == SafetyState.BLOCKED and (
        ctx.get("kill_switch_on", False) or ctx.get("critical_failure", False)
    ):
        return allow_transition(
            from_state.value,
            to_state.value,
            side_effects=("block_new_order_creation",),
        )

    delta = _SEVERITY[to_state] - _SEVERITY[from_state]
    if delta > 1:
        return block_transition(from_state.value, to_state.value, "SAFETY_ESCALATION_TOO_LARGE")
    if delta < -1 and not ctx.get("recovery_confirmed", False):
        return block_transition(from_state.value, to_state.value, "RECOVERY_CONFIRMATION_REQUIRED")

    return allow_transition(from_state.value, to_state.value)
