from __future__ import annotations
from datetime import datetime, timezone
from services.admin.kill_switch import get_state as get_kill, set_armed
from services.admin.config_editor import load_user_yaml, save_user_yaml
from services.execution.event_log import log_event
from services.run_context import run_id

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def status() -> dict:
    cfg = load_user_yaml()
    risk = cfg.get("risk") if isinstance(cfg.get("risk"), dict) else {}
    ks = get_kill()
    return {"ts": _now(), "run_id": run_id(), "risk_enable_live": bool(risk.get("enable_live", False)), "kill_switch_armed": bool(ks.get("armed", True)), "kill_switch": ks}

def disable_live_now(note: str = "wizard_disable_live") -> dict:
    cfg = load_user_yaml()
    risk = cfg.get("risk") if isinstance(cfg.get("risk"), dict) else {}
    prev = status()
    new_cfg = dict(cfg)
    new_risk = dict(risk)
    new_risk["enable_live"] = False
    new_cfg["risk"] = new_risk
    save_out = save_user_yaml(new_cfg, create_backup=True, dry_run=False)
    if not save_out.get("ok"):
        return {"ok": False, "reason": "config_save_failed", "save": save_out, "prev": prev}
    ks2 = set_armed(True, note=str(note))
    try:
        log_event("system", "GLOBAL", "live_disabled", ref_id=None, payload={"ts": _now(), "run_id": run_id(), "pre": prev, "post": {"risk_enable_live": False, "kill_switch": ks2}, "config_backup": save_out.get("backup"), "note": str(note)})
    except Exception:
        pass
    return {"ok": True, "prev": prev, "post": status(), "save": save_out, "kill_switch": ks2}
