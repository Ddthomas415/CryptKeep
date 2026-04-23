from __future__ import annotations

from typing import Any


LIVE_QUEUE_TERMINAL_STATUSES = {"filled", "canceled", "cancelled", "rejected", "error"}
RECONCILER_LIVE_QUEUE_TARGETS = {"rejected", "error"}
RECONCILER_LIVE_QUEUE_SOURCES = {"submitted"}
EXECUTION_STORE_STATUS_TRANSITIONS = {
    "pending": {"submitted", "canceled", "error"},
    "submitted": {"filled", "canceled", "error", "partially_filled"},
    "partially_filled": {"filled", "canceled", "error"},
    "filled": set(),
    "canceled": set(),
    "error": set(),
}


class IntentLifecycleViolation(Exception):
    pass


def normalize_live_queue_status(status: Any) -> str:
    return str(status or "").strip().lower()


def normalize_execution_store_status(status: Any) -> str:
    return str(status or "").strip().lower()


def execution_store_transition_allowed(current_status: Any, next_status: Any) -> bool:
    current = normalize_execution_store_status(current_status)
    nxt = normalize_execution_store_status(next_status)
    if current == nxt:
        return True
    return nxt in EXECUTION_STORE_STATUS_TRANSITIONS.get(current, set())


def validate_reconciler_live_queue_transition(
    *,
    current_status: Any,
    next_status: Any,
) -> str:
    current = normalize_live_queue_status(current_status)
    nxt = normalize_live_queue_status(next_status)
    if nxt not in RECONCILER_LIVE_QUEUE_TARGETS:
        raise IntentLifecycleViolation(
            f"blocked live queue transition: unsupported reconciler target {nxt!r}"
        )
    if current in LIVE_QUEUE_TERMINAL_STATUSES:
        raise IntentLifecycleViolation(
            f"blocked live queue transition: terminal status {current!r} is immutable"
        )
    if current not in RECONCILER_LIVE_QUEUE_SOURCES:
        raise IntentLifecycleViolation(
            f"blocked live queue transition: invalid source {current!r} for {nxt!r}"
        )
    return nxt
