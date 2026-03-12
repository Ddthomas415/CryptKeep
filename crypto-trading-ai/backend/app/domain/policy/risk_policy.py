from __future__ import annotations

from backend.app.domain.state_machines.safety import SafetyState


RISK_REDUCING_ACTIONS = {"close_position", "reduce_position", "cancel_order"}


def risk_allows_action(
    risk_state: SafetyState,
    action: str,
    *,
    kill_switch_on: bool = False,
) -> tuple[bool, str | None]:
    if kill_switch_on and action not in RISK_REDUCING_ACTIONS:
        return False, "KILL_SWITCH_ACTIVE"

    if risk_state == SafetyState.BLOCKED and action not in RISK_REDUCING_ACTIONS:
        return False, "RISK_STATE_BLOCKED"
    if risk_state == SafetyState.PAUSED and action in {"submit_live_order", "submit_paper_order"}:
        return False, "RISK_STATE_PAUSED"
    if risk_state == SafetyState.RESTRICTED and action in {"submit_live_order"}:
        return False, "RISK_STATE_RESTRICTED"
    return True, None
