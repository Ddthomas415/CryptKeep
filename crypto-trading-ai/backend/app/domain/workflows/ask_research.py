from __future__ import annotations

from backend.app.domain.workflows.common import (
    WorkflowEntity,
    WorkflowResult,
    workflow_blocked,
    workflow_success,
)


def execute_ask_research_workflow(context: dict) -> WorkflowResult:
    question = str(context.get("question", "")).strip()
    asset = str(context.get("asset", "")).strip().upper()

    if not question:
        return workflow_blocked(
            code="QUESTION_REQUIRED",
            message="Research question is required.",
            next_actions=["Provide a non-empty research query."],
        )

    query_id = context.get("query_id", "rq_stub")
    explanation_id = context.get("explanation_id", "exp_stub")
    return workflow_success(
        code="RESEARCH_EXPLANATION_GENERATED",
        message="Research explanation generated from current sources.",
        affected_entities=[
            WorkflowEntity(type="research_query", id=str(query_id), new_state="received"),
            WorkflowEntity(type="explanation", id=str(explanation_id), new_state="generated"),
            WorkflowEntity(type="asset", id=asset or "UNKNOWN"),
        ],
    )
