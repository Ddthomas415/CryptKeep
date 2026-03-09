from __future__ import annotations

from typing import Tuple, Dict, Any

from services.config_loader import load_user_config
from services.admin.kill_switch import get_state as kill_state
from services.execution.live_arming import is_live_enabled

def live_allowed() -> tuple[bool, str, dict]:
    '''
    Returns (allowed, reason, details).
    Allowed iff:
      - kill switch is DISARMED (armed == False)
      - live trading is enabled in the normalized config contract
    '''
    ks = kill_state()
    if bool(ks.get("armed", True)):
        return False, "kill_switch_armed", {"kill_switch": ks}

    cfg = load_user_config()
    live_enabled = is_live_enabled(cfg)
    if not live_enabled:
        return False, "risk_enable_live_false", {"live_enabled": False, "risk": {"enable_live": False}}

    return True, "ok", {"kill_switch": ks, "live_enabled": True, "risk": {"enable_live": True}}
