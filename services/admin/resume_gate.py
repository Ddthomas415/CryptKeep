from __future__ import annotations

from typing import Any, Dict

from services.admin.kill_switch import set_armed
from services.admin.live_guard import live_allowed


def resume_if_safe(*, note: str = "resume_if_safe") -> Dict[str, Any]:
    """
    Disarm kill switch only when live guard checks pass.
    Returns a structured status payload for dashboard callers.
    """
    allowed, reason, details = live_allowed()
    if not bool(allowed):
        return {"ok": False, "resumed": False, "reason": str(reason), "details": dict(details or {})}
    state = set_armed(False, note=note)
    return {"ok": True, "resumed": True, "reason": "ok", "kill_switch": state, "details": dict(details or {})}
