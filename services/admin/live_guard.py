from __future__ import annotations

from typing import Tuple, Dict, Any

from services.config_loader import load_user_config
from services.admin.kill_switch import get_state as kill_state
from services.admin.system_guard import get_state as get_system_guard_state
from services.execution.live_arming import is_live_enabled


def live_allowed(
    *,
    allow_kill_switch_armed: bool = False,
    allow_system_guard_halted: bool = False,
) -> tuple[bool, str, dict]:
    '''
    Returns (allowed, reason, details).
    Allowed iff:
      - system guard is not HALTING, and not HALTED unless explicitly allowed
      - kill switch is DISARMED (armed == False), unless explicitly allowed
      - live trading is enabled in the normalized config contract
    '''
    ks = kill_state()
    system_guard = get_system_guard_state(fail_closed=False)
    guard_state = str(system_guard.get("state") or "").upper().strip()
    details: dict[str, Any] = {"kill_switch": ks, "system_guard": system_guard}

    if guard_state == "HALTING":
        return False, "system_guard_halting", details
    if guard_state == "HALTED" and not bool(allow_system_guard_halted):
        return False, "system_guard_halted", details
    if bool(ks.get("armed", True)) and not bool(allow_kill_switch_armed):
        return False, "kill_switch_armed", details

    cfg = load_user_config()
    live_enabled = is_live_enabled(cfg)
    if not live_enabled:
        details.update({"live_enabled": False, "risk": {"enable_live": False}})
        return False, "risk_enable_live_false", details

    details.update({"live_enabled": True, "risk": {"enable_live": True}})
    return True, "ok", details
