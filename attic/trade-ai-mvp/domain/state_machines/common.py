from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Generic, TypeVar


TState = TypeVar("TState", bound=StrEnum)


@dataclass(frozen=True)
class TransitionResult(Generic[TState]):
    allowed: bool
    from_state: TState
    to_state: TState
    reason: str = ""
    side_effects: list[str] = field(default_factory=list)


def allow_transition(
    *,
    from_state: TState,
    to_state: TState,
    reason: str = "",
    side_effects: list[str] | None = None,
) -> TransitionResult[TState]:
    return TransitionResult(
        allowed=True,
        from_state=from_state,
        to_state=to_state,
        reason=reason,
        side_effects=list(side_effects or []),
    )


def deny_transition(
    *,
    from_state: TState,
    to_state: TState,
    reason: str,
    side_effects: list[str] | None = None,
) -> TransitionResult[TState]:
    return TransitionResult(
        allowed=False,
        from_state=from_state,
        to_state=to_state,
        reason=str(reason),
        side_effects=list(side_effects or []),
    )


def build_transition_audit_event(
    *,
    entity_type: str,
    entity_id: str,
    transition: TransitionResult[Any],
    actor_type: str,
    actor_id: str,
    request_id: str | None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "previous_state": str(transition.from_state.value),
        "next_state": str(transition.to_state.value),
        "allowed": bool(transition.allowed),
        "reason": str(transition.reason),
        "actor_type": str(actor_type),
        "actor_id": str(actor_id),
        "request_id": request_id,
        "context": dict(context or {}),
    }
