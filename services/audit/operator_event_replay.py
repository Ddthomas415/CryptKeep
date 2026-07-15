from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.audit.operator_event_journal import load_operator_events, operator_event_journal_path

ARM_ACTIONS = {"live_enable", "live_resume"}
HALT_ACTIONS = {"live_disable", "live_halt"}
LIVE_TARGET = "live_trading"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _nested_get(obj: Any, path: tuple[str, ...]) -> Any:
    cur = obj
    for part in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _is_live_event(event: dict[str, Any], actions: set[str]) -> bool:
    return str(event.get("target") or "") == LIVE_TARGET and str(event.get("action") or "") in actions


def _is_arm_event(event: dict[str, Any]) -> bool:
    if not _is_live_event(event, ARM_ACTIONS):
        return False
    return bool(
        _nested_get(event, ("post_state", "armed"))
        or _nested_get(event, ("post_state", "armed_state", "armed"))
        or _nested_get(event, ("post_state", "status", "armed"))
    )


def _is_halt_event(event: dict[str, Any]) -> bool:
    if not _is_live_event(event, HALT_ACTIONS):
        return False
    states = {
        str(_nested_get(event, ("post_state", "system_guard", "state")) or "").upper(),
        str(_nested_get(event, ("post_state", "status", "system_guard", "state")) or "").upper(),
        str(_nested_get(event, ("post_state", "status", "kill_switch", "armed")) or ""),
        str(_nested_get(event, ("post_state", "kill_switch", "armed")) or ""),
    }
    return "HALTED" in states or "True" in states


def _event_summary(event: dict[str, Any], *, index: int) -> dict[str, Any]:
    return {
        "index": index,
        "event_id": event.get("event_id"),
        "timestamp": event.get("timestamp"),
        "action": event.get("action"),
        "target": event.get("target"),
        "result": event.get("result"),
        "reason": event.get("reason"),
        "source": event.get("source"),
    }


def replay_live_arm_to_halt(path: Path | None = None) -> dict[str, Any]:
    src = Path(path) if path is not None else operator_event_journal_path()
    if not src.exists():
        return {
            "created": _utc_now(),
            "ok": False,
            "path": str(src),
            "event_count": 0,
            "reason": "operator_event_journal_missing",
            "arm_event": None,
            "halt_event": None,
        }

    try:
        events = load_operator_events(src)
    except Exception as exc:
        return {
            "created": _utc_now(),
            "ok": False,
            "path": str(src),
            "event_count": 0,
            "reason": f"operator_event_journal_unreadable:{type(exc).__name__}",
            "arm_event": None,
            "halt_event": None,
        }

    arm: tuple[int, dict[str, Any]] | None = None
    for index, event in enumerate(events):
        if _is_arm_event(event):
            arm = (index, event)
            break
    if arm is None:
        return {
            "created": _utc_now(),
            "ok": False,
            "path": str(src),
            "event_count": len(events),
            "reason": "missing_live_arm_event",
            "arm_event": None,
            "halt_event": None,
        }

    halt: tuple[int, dict[str, Any]] | None = None
    for index, event in enumerate(events[arm[0] + 1 :], start=arm[0] + 1):
        if _is_halt_event(event):
            halt = (index, event)
            break
    if halt is None:
        return {
            "created": _utc_now(),
            "ok": False,
            "path": str(src),
            "event_count": len(events),
            "reason": "missing_live_halt_event_after_arm",
            "arm_event": _event_summary(arm[1], index=arm[0]),
            "halt_event": None,
        }

    return {
        "created": _utc_now(),
        "ok": True,
        "path": str(src),
        "event_count": len(events),
        "reason": "ok",
        "arm_event": _event_summary(arm[1], index=arm[0]),
        "halt_event": _event_summary(halt[1], index=halt[0]),
    }


def report_to_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True)
