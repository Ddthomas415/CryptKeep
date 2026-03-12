from __future__ import annotations

from backend.app.domain.policy.roles import Role
from backend.app.domain.policy.terminal_policy import evaluate_terminal_command
from backend.app.domain.state_machines.mode import Mode
from backend.app.domain.state_machines.safety import SafetyState
from backend.app.domain.workflows.common import (
    WorkflowEntity,
    WorkflowResult,
    workflow_blocked,
    workflow_success,
)


def execute_terminal_workflow(context: dict) -> WorkflowResult:
    command = str(context.get("command", "")).strip()
    if not command:
        return workflow_blocked(
            code="COMMAND_REQUIRED",
            message="Terminal command is required.",
        )

    role = Role(context.get("role", Role.VIEWER.value))
    mode = Mode(context.get("mode", Mode.RESEARCH_ONLY.value))
    risk_state = SafetyState(context.get("risk_state", SafetyState.SAFE.value))
    kill_switch_on = bool(context.get("kill_switch_on", False))

    decision = evaluate_terminal_command(
        role=role,
        command=command,
        mode=mode,
        risk_state=risk_state,
        kill_switch_on=kill_switch_on,
    )
    if not decision.allowed:
        return workflow_blocked(
            code=decision.reason_codes[0] if decision.reason_codes else "COMMAND_BLOCKED",
            message=decision.user_message,
        )

    return workflow_success(
        code="TERMINAL_COMMAND_ACCEPTED",
        message=decision.user_message,
        affected_entities=[
            WorkflowEntity(
                type="terminal_command",
                id=str(context.get("command_id", "cmd_stub")),
                new_state="accepted",
            )
        ],
        next_actions=["Require user confirmation"] if decision.requires_approval else [],
    )
