from __future__ import annotations

from services.admin.kill_switch import get_state, set_armed


def set_kill_switch(armed: bool, reason: str = "manual") -> dict:
    payload = set_armed(bool(armed), note=str(reason or "manual"))
    return {"ok": True, "armed": bool(payload.get("armed", False)), "state": payload}


def is_kill_switch_on() -> bool:
    st = get_state() or {}
    return bool(st.get("armed", True))


def get_kill_switch() -> dict:
    st = get_state() or {}
    return {"ok": True, "armed": bool(st.get("armed", True)), "state": st}

