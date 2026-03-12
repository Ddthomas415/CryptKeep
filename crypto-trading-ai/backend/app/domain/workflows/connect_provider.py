from __future__ import annotations

from backend.app.domain.workflows.common import (
    WorkflowEntity,
    WorkflowResult,
    workflow_blocked,
    workflow_success,
)


def execute_connect_provider_workflow(context: dict) -> WorkflowResult:
    provider = str(context.get("provider", "")).strip().lower()
    config = context.get("config") or {}

    if not provider:
        return workflow_blocked(
            code="PROVIDER_REQUIRED",
            message="Provider is required.",
            next_actions=["Choose a provider before saving."],
        )
    if provider in {"newsapi", "messari", "etherscan"} and not config.get("api_key"):
        return workflow_blocked(
            code="PROVIDER_KEY_REQUIRED",
            message="API key is required for this provider.",
            next_actions=["Add provider API key and test connection."],
        )

    provider_id = str(context.get("provider_id", f"prov_{provider}_stub"))
    return workflow_success(
        code="PROVIDER_CONNECTED",
        message="Provider connection saved.",
        affected_entities=[
            WorkflowEntity(type="provider_connection", id=provider_id, new_state="connected")
        ],
    )
