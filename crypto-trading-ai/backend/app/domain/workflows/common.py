from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


WorkflowState = Literal["success", "blocked", "partial_success", "failure"]


class WorkflowEntity(BaseModel):
    type: str
    id: str
    new_state: str | None = None


class WorkflowResult(BaseModel):
    success: bool
    state: WorkflowState
    code: str
    message: str
    affected_entities: list[WorkflowEntity] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


def workflow_success(
    *,
    code: str,
    message: str,
    affected_entities: list[WorkflowEntity] | None = None,
    next_actions: list[str] | None = None,
) -> WorkflowResult:
    return WorkflowResult(
        success=True,
        state="success",
        code=code,
        message=message,
        affected_entities=affected_entities or [],
        next_actions=next_actions or [],
    )


def workflow_partial_success(
    *,
    code: str,
    message: str,
    affected_entities: list[WorkflowEntity] | None = None,
    next_actions: list[str] | None = None,
) -> WorkflowResult:
    return WorkflowResult(
        success=True,
        state="partial_success",
        code=code,
        message=message,
        affected_entities=affected_entities or [],
        next_actions=next_actions or [],
    )


def workflow_blocked(
    *,
    code: str,
    message: str,
    next_actions: list[str] | None = None,
) -> WorkflowResult:
    return WorkflowResult(
        success=False,
        state="blocked",
        code=code,
        message=message,
        next_actions=next_actions or [],
    )


def workflow_failure(
    *,
    code: str,
    message: str,
    next_actions: list[str] | None = None,
) -> WorkflowResult:
    return WorkflowResult(
        success=False,
        state="failure",
        code=code,
        message=message,
        next_actions=next_actions or [],
    )
