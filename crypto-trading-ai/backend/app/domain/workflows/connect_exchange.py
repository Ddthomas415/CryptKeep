from __future__ import annotations

from backend.app.domain.workflows.common import (
    WorkflowEntity,
    WorkflowResult,
    workflow_blocked,
    workflow_partial_success,
    workflow_success,
)


def execute_connect_exchange_workflow(context: dict) -> WorkflowResult:
    provider = str(context.get("provider", "")).strip().lower()
    label = str(context.get("label", "")).strip()
    credentials = context.get("credentials") or {}

    if not provider or not label:
        return workflow_blocked(
            code="INVALID_CONNECTION_INPUT",
            message="Provider and label are required.",
            next_actions=["Select a provider and enter a connection label."],
        )
    if not credentials.get("api_key") or not credentials.get("api_secret"):
        return workflow_blocked(
            code="INVALID_CREDENTIALS",
            message="API key and secret are required.",
            next_actions=["Enter valid credentials and rerun connection test."],
        )

    read_only = bool(context.get("read_only", False) or credentials.get("read_only", False))
    connection_id = str(context.get("connection_id", f"conn_{provider}_stub"))
    if read_only:
        return workflow_partial_success(
            code="CONNECTION_SAVED_READ_ONLY",
            message="Exchange connected in read-only mode.",
            affected_entities=[
                WorkflowEntity(type="exchange_connection", id=connection_id, new_state="connected")
            ],
            next_actions=["Enable trade permissions later if policy allows."],
        )

    return workflow_success(
        code="CONNECTION_SAVED",
        message="Exchange connection saved and ready.",
        affected_entities=[WorkflowEntity(type="exchange_connection", id=connection_id, new_state="connected")],
    )
