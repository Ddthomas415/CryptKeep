from __future__ import annotations

from backend.app.domain.policy.roles import Role, role_allows_action
from backend.app.domain.state_machines.mode import Mode, can_transition_mode
from backend.app.domain.workflows.common import (
    WorkflowEntity,
    WorkflowResult,
    workflow_blocked,
    workflow_success,
)


def execute_switch_mode_workflow(context: dict) -> WorkflowResult:
    current_mode = Mode(context.get("current_mode", Mode.RESEARCH_ONLY.value))
    target_mode = Mode(context.get("target_mode", Mode.RESEARCH_ONLY.value))
    role = Role(context.get("role", Role.VIEWER.value))

    if target_mode == Mode.LIVE_AUTO and not role_allows_action(role, "switch_mode_live_auto"):
        return workflow_blocked(
            code="ROLE_NOT_ALLOWED",
            message="Only owner can switch to live_auto mode.",
        )

    transition = can_transition_mode(
        current_mode,
        target_mode,
        context={
            "has_trade_connection": bool(context.get("has_trade_connection", False)),
            "risk_configured": bool(context.get("risk_configured", False)),
            "kill_switch_on": bool(context.get("kill_switch_on", False)),
            "explicit_confirmation": bool(context.get("explicit_confirmation", False)),
        },
    )
    if not transition.allowed:
        return workflow_blocked(
            code=transition.reason or "MODE_BLOCKED",
            message=f"Mode transition blocked: {transition.reason}",
            next_actions=list(transition.side_effects),
        )

    return workflow_success(
        code="MODE_SWITCHED",
        message=f"Mode switched from {current_mode.value} to {target_mode.value}.",
        affected_entities=[
            WorkflowEntity(
                type="workspace_mode",
                id=str(context.get("workspace_id", "ws_stub")),
                new_state=target_mode.value,
            )
        ],
        next_actions=list(transition.side_effects),
    )
