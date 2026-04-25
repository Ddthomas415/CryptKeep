from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from services.execution.intent_lifecycle import (
    IntentLifecycleViolation,
    validate_reconciler_live_queue_transition,
    validate_submit_owner_live_queue_transition,
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


def _validated_submit_owner_live_queue_status(
    *, current_status: Any, next_status: Any, ctx: LiveStateContext | None
) -> str:
    _authorize_state_write(ctx)
    if ctx is None or ctx.authority != "INTENT_CONSUMER":
        raise LiveStateViolation("blocked live queue write: intent-consumer authority required")
    try:
        return validate_submit_owner_live_queue_transition(
            current_status=current_status,
            next_status=next_status,
        )
    except IntentLifecycleViolation as exc:
        raise LiveStateViolation(str(exc)) from exc


def update_live_queue_status_as_intent_consumer(
    qdb: Any,
    intent: dict[str, Any],
    status: str,
    *,
    ctx: LiveStateContext | None,
    last_error: str | None = None,
    client_order_id: str | None = None,
    exchange_order_id: str | None = None,
) -> None:
    intent_id = str(intent.get("intent_id") or "").strip()
    if not intent_id:
        raise LiveStateViolation("blocked live queue transition: missing intent_id")
    nxt = _validated_submit_owner_live_queue_status(
        current_status=intent.get("status"),
        next_status=status,
        ctx=ctx,
    )
    kwargs = {"last_error": last_error}
    if client_order_id is not None:
        kwargs["client_order_id"] = client_order_id
    if exchange_order_id is not None:
        kwargs["exchange_order_id"] = exchange_order_id
    qdb.update_status(intent_id, nxt, **kwargs)


def paper_queue_status(
    qdb: Any,
    intent: dict[str, Any],
    status: str,
    *,
    ctx: LiveStateContext | None,
    last_error: str | None = None,
    client_order_id: str | None = None,
    linked_order_id: str | None = None,
) -> None:
    intent_id = str(intent.get("intent_id") or "").strip()
    if not intent_id:
        raise LiveStateViolation("blocked paper queue transition: missing intent_id")

    _authorize_state_write(ctx)

    kwargs = {"last_error": last_error}
    if client_order_id is not None:
        kwargs["client_order_id"] = client_order_id
    if linked_order_id is not None:
        kwargs["linked_order_id"] = linked_order_id

    qdb.update_status(intent_id, status, **kwargs)

def paper_queue_hold_release(
    qdb: Any,
    intent: dict[str, Any],
    status: str,
    *,
    ctx: LiveStateContext | None,
    reason: str | None = None,
) -> None:
    """Narrow helper for hold/release transitions on the paper queue surface."""
    if status not in ("held", "queued"):
        raise ValueError("paper_queue_hold_release only accepts held/queued")
    paper_queue_status(qdb, intent, status, ctx=ctx, last_error=reason)
