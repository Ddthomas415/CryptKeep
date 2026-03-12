from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class TransitionResult:
    allowed: bool
    from_state: str
    to_state: str
    reason: str | None = None
    side_effects: tuple[str, ...] = field(default_factory=tuple)


def allow_transition(
    from_state: str,
    to_state: str,
    *,
    side_effects: tuple[str, ...] = (),
    reason: str | None = None,
) -> TransitionResult:
    return TransitionResult(
        allowed=True,
        from_state=from_state,
        to_state=to_state,
        reason=reason,
        side_effects=side_effects,
    )


def block_transition(from_state: str, to_state: str, reason: str) -> TransitionResult:
    return TransitionResult(
        allowed=False,
        from_state=from_state,
        to_state=to_state,
        reason=reason,
    )


def build_transition_audit_event(
    *,
    entity_type: str,
    entity_id: str,
    result: TransitionResult,
    actor_type: str,
    actor_id: str,
    request_id: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "previous_state": result.from_state,
        "next_state": result.to_state,
        "actor_type": actor_type,
        "actor_id": actor_id,
        "reason": result.reason or "",
        "request_id": request_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "context": context or {},
    }
