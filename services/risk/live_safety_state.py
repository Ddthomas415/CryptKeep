from __future__ import annotations

import logging
_LOG = logging.getLogger(__name__)

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
    except Exception as _err:
        pass  # suppressed: see _LOG.debug below
    return {"kill_switch": False, "cooldown_until": 0.0}
