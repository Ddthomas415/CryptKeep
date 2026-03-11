from __future__ import annotations

from typing import Any, Dict

from services.risk import killswitch


def snapshot() -> Dict[str, Any]:
    """Compatibility shim used by legacy execution guards."""
    try:
        snap = killswitch.snapshot()
        if isinstance(snap, dict):
            return {
                "kill_switch": bool(snap.get("kill_switch", False)),
                "cooldown_until": float(snap.get("cooldown_until", 0.0) or 0.0),
            }
    except Exception:
        pass
    return {"kill_switch": False, "cooldown_until": 0.0}
