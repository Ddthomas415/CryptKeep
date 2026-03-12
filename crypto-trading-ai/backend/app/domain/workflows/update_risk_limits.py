from __future__ import annotations

from backend.app.domain.policy.roles import Role, role_allows_action
from backend.app.domain.workflows.common import (
    WorkflowEntity,
    WorkflowResult,
    workflow_blocked,
    workflow_success,
)


def execute_update_risk_limits_workflow(context: dict) -> WorkflowResult:
    role = Role(context.get("role", Role.VIEWER.value))
    limits = context.get("limits") or {}

    if not role_allows_action(role, "edit_risk_limits"):
        return workflow_blocked(
            code="ROLE_NOT_ALLOWED",
            message="Only owner can update risk limits in this starter policy.",
        )
    if not limits:
        return workflow_blocked(
            code="LIMITS_REQUIRED",
            message="Risk limits payload is required.",
        )

    max_daily_loss_pct = float(limits.get("max_daily_loss_pct", 0))
    if max_daily_loss_pct <= 0 or max_daily_loss_pct > 100:
        return workflow_blocked(
            code="INVALID_LIMITS",
            message="max_daily_loss_pct must be between 0 and 100.",
        )

    return workflow_success(
        code="RISK_LIMITS_UPDATED",
        message="Risk limits updated.",
        affected_entities=[
            WorkflowEntity(
                type="risk_limits",
                id=str(context.get("workspace_id", "ws_stub")),
                new_state="updated",
            )
        ],
    )
