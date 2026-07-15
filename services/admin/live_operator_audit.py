from __future__ import annotations

import logging
from typing import Any

from services.audit.operator_event_journal import append_operator_event

_LOG = logging.getLogger(__name__)


def record_live_disable_event(
    *,
    actor: str = "operator",
    source: str,
    reason: str,
    pre_state: dict[str, Any],
    post_state: dict[str, Any],
    result: str = "success",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Best-effort operator journal hook for safety-increasing live-disable paths.

    Disable/halt must not be blocked by audit storage problems; callers surface
    the failure in their returned payload while preserving the safety action.
    """
    try:
        event = append_operator_event(
            actor=actor,
            action="live_disable",
            target="live_trading",
            result=result,
            reason=reason,
            pre_state=pre_state,
            post_state=post_state,
            source=source,
            extra=extra or {},
        )
        return {
            "ok": True,
            "event_id": event.get("event_id"),
            "path": event.get("path"),
        }
    except Exception as exc:
        _LOG.warning("live disable operator event journal failed: %s: %s", type(exc).__name__, exc)
        return {"ok": False, "reason": f"operator_event_write_failed:{type(exc).__name__}"}
