from __future__ import annotations
from datetime import datetime, timezone
from services.admin.live_disable_wizard import disable_live_now, status
from services.admin.config_editor import load_user_yaml

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def auto_disable_if_needed() -> dict:
    cfg = load_user_yaml()
    safety = cfg.get("safety") if isinstance(cfg.get("safety"), dict) else {}
    auto = bool(safety.get("auto_disable_live_on_start", True))
    st = status()
    if not auto: return {"ok": True, "did_action": False, "reason": "auto_disable_disabled_in_config", "status": st, "ts": _now()}
    enable_live = bool(st.get("risk_enable_live", False))
    ks_armed = bool(st.get("kill_switch_armed", True))
    guard_state = str((st.get("system_guard") or {}).get("state") or "").upper().strip()
    guard_safe = guard_state in {"HALTING", "HALTED"}
    if enable_live or (not ks_armed) or (not guard_safe):
        out = disable_live_now(note="auto_recovery_on_start")
        return {"ok": bool(out.get("ok")), "did_action": True, "reason": "auto_recovery_on_start", "result": out, "ts": _now()}
    return {"ok": True, "did_action": False, "reason": "already_safe", "status": st, "ts": _now()}
