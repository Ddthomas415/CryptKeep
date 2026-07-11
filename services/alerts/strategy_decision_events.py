"""Strategy decision-change alerting (Active backlog #23).

Notification-only by design: this module reads the strategy evidence comparison
that was already computed by the evidence cycle and dispatches an operator
alert when a strategy decision changes versus the previous persisted evidence
artifact. Alert failures must never affect evidence persistence.
"""
from __future__ import annotations

from typing import Any

_DECISION_WEIGHT: dict[str, int] = {
    "keep": 4,
    "improve": 3,
    "freeze": 2,
    "retire": 1,
}


def _send(level: str, message: str, payload: dict | None) -> None:
    from services.alerts.alert_dispatcher import send_alert
    from services.config_loader import load_runtime_trading_config

    try:
        cfg = load_runtime_trading_config()
    except Exception:
        cfg = {}
    send_alert(
        cfg=cfg if isinstance(cfg, dict) else {},
        level=level,
        message=message,
        payload=payload,
    )


def _decision_weight(value: Any) -> int:
    return int(_DECISION_WEIGHT.get(str(value or "").strip().lower(), 0))


def _severity_for_changes(changes: list[dict[str, Any]]) -> str:
    """Return the highest-severity level needed for the decision changes."""
    level = "info"
    for change in changes:
        current = str(change.get("current_decision") or "").strip().lower()
        previous = str(change.get("previous_decision") or "").strip().lower()
        if current == "retire":
            return "critical"
        if previous and _decision_weight(current) < _decision_weight(previous):
            level = "warning"
    return level


def alert_strategy_decision_changes(comparison: dict[str, Any] | None) -> bool:
    """Alert once when persisted strategy decisions change.

    Rules:
    - no previous persisted evidence -> silent baseline
    - only decision changes alert; rank/score-only movement stays silent
    - new strategy decisions after a baseline alert at info level
    - degraded decisions alert warning; retire decisions alert critical
    - never raises; returns True iff an alert was dispatched
    """
    try:
        payload = dict(comparison or {})
        if not bool(payload.get("has_previous")):
            return False

        decision_changes = [
            dict(item)
            for item in list(payload.get("changes") or [])
            if isinstance(item, dict) and bool(item.get("decision_changed"))
        ]
        if not decision_changes:
            return False

        alert_payload = {
            "previous_as_of": payload.get("previous_as_of"),
            "current_as_of": payload.get("current_as_of"),
            "top_strategy_previous": payload.get("top_strategy_previous"),
            "top_strategy_current": payload.get("top_strategy_current"),
            "top_strategy_changed": bool(payload.get("top_strategy_changed")),
            "decision_change_count": int(len(decision_changes)),
            "changes": decision_changes,
        }
        _send(
            _severity_for_changes(decision_changes),
            "strategy_decisions:changed",
            alert_payload,
        )
        return True
    except Exception:
        return False
