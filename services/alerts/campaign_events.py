"""Campaign stop/failure event alerting (Active backlog #23; the campaign
stop/failure half of the remaining alert lane).

Notification-only by design: mirrors services/alerts/paper_gate_events.py:
nothing here influences trading, gating, evidence, or campaign-status
advancement. Every entry point is best-effort and never raises; a raising
alert channel must not block a campaign status write. Channel selection lives
in the existing alert dispatcher; with no channels configured the proven local
JSONL fallback still records the event.

Fires once per TRANSITION into an operator-actionable blocked/stop/failure
state (not once per status write), with the first observation establishing a
silent baseline.
"""
from __future__ import annotations

from typing import Any

# Campaign states that warrant an operator wake-up, mapped to level.
# "blocked"/"stopped" are warning-level operator-action states;
# "failed"/"error"/"aborted" are abnormal ends (critical). Normal
# "completed" is intentionally NOT alerted (a clean finish is not an incident).
_STOP_FAILURE_LEVELS: dict[str, str] = {
    "blocked": "warning",
    "failed": "critical",
    "error": "critical",
    "aborted": "critical",
    "stopped": "warning",
}

_CAMPAIGN_ENDED_STATUSES = {"completed", "stopped", "failed", "error", "aborted"}


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


def _emit_campaign_ended_event(prev: str, new: str, payload: dict[str, Any] | None) -> None:
    if new not in _CAMPAIGN_ENDED_STATUSES:
        return
    try:
        from services.events.platform_event_journal import append_platform_event

        event_payload = dict(payload or {})
        event_payload.update(
            {
                "prev_status": prev,
                "new_status": new,
                "reason": event_payload.get("reason") or "",
            }
        )
        append_platform_event(
            event_type="CampaignEnded",
            producer="services.alerts.campaign_events",
            source="campaign_status_transition",
            strategy_id=str(event_payload.get("strategy_id") or ""),
            run_id=str(event_payload.get("run_id") or event_payload.get("session_id") or ""),
            payload=event_payload,
        )
    except Exception:
        return


def alert_campaign_status_transition(
    prev_status: str,
    new_status: str,
    payload: dict[str, Any] | None = None,
) -> bool:
    """Alert once per transition INTO a stop/failure state.

    Rules (matching the paper_gate_events contract):
    - first observation (no prior status) is a silent baseline -> no alert
    - only a genuine change of status can alert (prev == new -> no alert)
    - only transitions into a blocked/stop/failure state alert; transitions
      into running/completed/other states do not
    - never raises; returns True iff an alert was dispatched

    The caller is responsible for invoking this only AFTER the status write has
    succeeded, so a raising channel cannot block campaign advancement.
    """
    try:
        prev = str(prev_status or "").strip().lower()
        new = str(new_status or "").strip().lower()

        # First-run baseline: no previous status means nothing to transition
        # FROM, so stay silent (mirrors gate-events baseline behavior).
        if not prev:
            return False
        if prev == new:
            return False

        alerted = False
        level = _STOP_FAILURE_LEVELS.get(new)
        if level is not None:
            try:
                _send(level, f"campaign:{new}", payload)
                alerted = True
            except Exception:
                alerted = False
        _emit_campaign_ended_event(prev, new, payload)
        return alerted
    except Exception:
        return False
