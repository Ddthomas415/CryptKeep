from __future__ import annotations

from typing import Tuple, Dict, Any

from services.config_loader import load_user_config
from services.admin.kill_switch import get_state as kill_state

def live_allowed() -> tuple[bool, str, dict]:
    '''
    Returns (allowed, reason, details).
    Allowed iff:
      - kill switch is DISARMED (armed == False)
      - risk.enable_live == True
    '''
    ks = kill_state()
    if bool(ks.get("armed", True)):
        return False, "kill_switch_armed", {"kill_switch": ks}

    cfg = load_user_config()
    risk = cfg.get("risk") if isinstance(cfg.get("risk"), dict) else {}
    if not bool(risk.get("enable_live", False)):
        return False, "risk_enable_live_false", {"risk": {"enable_live": risk.get("enable_live", False)}}

    return True, "ok", {"kill_switch": ks, "risk": {"enable_live": True}}
