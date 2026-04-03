from __future__ import annotations

from typing import Any, Dict

from services.admin.kill_switch import set_armed
from services.admin.system_guard import set_state as set_system_guard_state
from services.admin.live_guard import live_allowed


def resume_if_safe(*, note: str = "resume_if_safe") -> Dict[str, Any]:
    """
    Restore RUNNING only when the live guard checks pass for a resumable state.
    Returns a structured status payload for dashboard callers.
    """
    allowed, reason, details = live_allowed(
        allow_kill_switch_armed=True,
        allow_system_guard_halted=True,
    )
    if not bool(allowed):
        return {"ok": False, "resumed": False, "reason": str(reason), "details": dict(details or {})}
    kill_switch = set_armed(False, note=note)
    try:
        system_guard = set_system_guard_state("RUNNING", writer="resume_gate", reason=str(note))
    except Exception as exc:
        rollback = set_armed(True, note=f"{note}:rollback_system_guard_failed")
        return {
            "ok": False,
            "resumed": False,
            "reason": f"system_guard_resume_failed:{type(exc).__name__}",
            "kill_switch": rollback,
            "details": dict(details or {}),
        }
    return {
        "ok": True,
        "resumed": True,
        "reason": "ok",
        "kill_switch": kill_switch,
        "system_guard": system_guard,
        "details": dict(details or {}),
    }
