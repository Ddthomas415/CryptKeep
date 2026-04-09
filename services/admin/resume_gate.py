from __future__ import annotations

import os
from typing import Any, Dict

from services.admin.kill_switch import set_armed
from services.admin.system_guard import set_state as set_system_guard_state
from services.admin.live_guard import live_allowed
from services.execution.live_arming import set_live_armed_state


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
    try:
        armed_state = set_live_armed_state(True, writer="resume_gate", reason=str(note))
    except Exception as exc:
        return {
            "ok": False,
            "resumed": False,
            "reason": f"live_arm_restore_failed:{type(exc).__name__}",
            "details": dict(details or {}),
        }
    os.environ["CBP_EXECUTION_ARMED"] = "YES"
    kill_switch = set_armed(False, note=note)
    try:
        system_guard = set_system_guard_state("RUNNING", writer="resume_gate", reason=str(note))
    except Exception as exc:
        os.environ.pop("CBP_EXECUTION_ARMED", None)
        rollback_arm = set_live_armed_state(False, writer="resume_gate", reason=f"{note}:rollback_system_guard_failed")
        rollback = set_armed(True, note=f"{note}:rollback_system_guard_failed")
        return {
            "ok": False,
            "resumed": False,
            "reason": f"system_guard_resume_failed:{type(exc).__name__}",
            "armed_state": rollback_arm,
            "kill_switch": rollback,
            "details": dict(details or {}),
        }
    return {
        "ok": True,
        "resumed": True,
        "reason": "ok",
        "armed_state": armed_state,
        "kill_switch": kill_switch,
        "system_guard": system_guard,
        "details": dict(details or {}),
    }
