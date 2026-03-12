from enum import Enum

from backend.app.domain.state_machines.common import (
    TransitionResult,
    allow_transition,
    block_transition,
    build_transition_audit_event,
)


class Mode(str, Enum):
    RESEARCH_ONLY = "research_only"
    PAPER = "paper"
    LIVE_APPROVAL = "live_approval"
    LIVE_AUTO = "live_auto"


ALLOWED_MODE_TRANSITIONS: set[tuple[Mode, Mode]] = {
    (Mode.RESEARCH_ONLY, Mode.PAPER),
    (Mode.RESEARCH_ONLY, Mode.LIVE_APPROVAL),
    (Mode.PAPER, Mode.RESEARCH_ONLY),
    (Mode.PAPER, Mode.LIVE_APPROVAL),
    (Mode.LIVE_APPROVAL, Mode.RESEARCH_ONLY),
    (Mode.LIVE_APPROVAL, Mode.PAPER),
    (Mode.LIVE_APPROVAL, Mode.LIVE_AUTO),
    (Mode.LIVE_AUTO, Mode.LIVE_APPROVAL),
    (Mode.LIVE_AUTO, Mode.PAPER),
    (Mode.LIVE_AUTO, Mode.RESEARCH_ONLY),
}


MODE_SIDE_EFFECTS: dict[Mode, tuple[str, ...]] = {
    Mode.RESEARCH_ONLY: (
        "cancel_pending_live_approvals",
        "block_new_order_submissions",
    ),
    Mode.PAPER: ("switch_execution_context_to_simulator",),
    Mode.LIVE_APPROVAL: ("enable_approval_queue",),
    Mode.LIVE_AUTO: ("enable_auto_execution_gate",),
}


def can_transition_mode(
    from_mode: Mode,
    to_mode: Mode,
    *,
    context: dict | None = None,
) -> TransitionResult:
    if from_mode == to_mode:
        return allow_transition(from_mode.value, to_mode.value, reason="no_op")

    if (from_mode, to_mode) not in ALLOWED_MODE_TRANSITIONS:
        return block_transition(from_mode.value, to_mode.value, "MODE_TRANSITION_NOT_ALLOWED")

    ctx = context or {}
    if to_mode in {Mode.LIVE_APPROVAL, Mode.LIVE_AUTO}:
        if not ctx.get("has_trade_connection", False):
            return block_transition(from_mode.value, to_mode.value, "MISSING_TRADE_CONNECTION")
        if not ctx.get("risk_configured", False):
            return block_transition(from_mode.value, to_mode.value, "RISK_NOT_CONFIGURED")
        if ctx.get("kill_switch_on", False):
            return block_transition(from_mode.value, to_mode.value, "KILL_SWITCH_ACTIVE")
        if not ctx.get("explicit_confirmation", False):
            return block_transition(from_mode.value, to_mode.value, "CONFIRMATION_REQUIRED")

    return allow_transition(
        from_mode.value,
        to_mode.value,
        side_effects=MODE_SIDE_EFFECTS.get(to_mode, ()),
    )


def build_mode_audit_event(
    *,
    mode_id: str,
    result: TransitionResult,
    actor_type: str,
    actor_id: str,
    request_id: str,
    context: dict | None = None,
) -> dict:
    return build_transition_audit_event(
        entity_type="mode",
        entity_id=mode_id,
        result=result,
        actor_type=actor_type,
        actor_id=actor_id,
        request_id=request_id,
        context=context,
    )
