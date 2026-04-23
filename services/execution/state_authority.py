from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from services.execution.intent_lifecycle import (
    IntentLifecycleViolation,
    validate_reconciler_live_queue_transition,
)

@dataclass(frozen=True)
class LiveStateContext:
    authority: Literal["INTENT_CONSUMER", "RECONCILER", "UNKNOWN"]
    origin: str = "unknown"

class LiveStateViolation(Exception):
    pass

def _authorize_state_write(ctx: LiveStateContext | None) -> None:
    if ctx is None or ctx.authority == "UNKNOWN":
        raise LiveStateViolation("blocked state write: missing or unknown authority")


def _validated_reconciler_live_queue_status(
    *, current_status: Any, next_status: Any, ctx: LiveStateContext | None
) -> str:
    _authorize_state_write(ctx)
    if ctx is None or ctx.authority != "RECONCILER":
        raise LiveStateViolation("blocked live queue write: reconciler authority required")
    try:
        return validate_reconciler_live_queue_transition(
            current_status=current_status,
            next_status=next_status,
        )
    except IntentLifecycleViolation as exc:
        raise LiveStateViolation(str(exc)) from exc


def update_live_queue_status_as_reconciler(
    qdb: Any,
    intent: dict[str, Any],
    status: str,
    *,
    ctx: LiveStateContext | None,
    last_error: str | None = None,
) -> None:
    intent_id = str(intent.get("intent_id") or "").strip()
    if not intent_id:
        raise LiveStateViolation("blocked live queue transition: missing intent_id")
    nxt = _validated_reconciler_live_queue_status(
        current_status=intent.get("status"),
        next_status=status,
        ctx=ctx,
    )
    qdb.update_status(intent_id, nxt, last_error=last_error)
