from __future__ import annotations
import os
from datetime import datetime
from services.admin.config_editor import load_user_yaml, save_user_yaml
from services.execution.live_arming import live_enabled_and_armed

AUDIT_LOG = Path("runtime/logs/live_arm_audit.log")

def _log_audit(action: str, success: bool, reason: str = "") -> None:
    ts = datetime.utcnow().isoformat()
    line = f"{ts} | {action} | success={success} | reason={reason}\n"
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_LOG, "a") as f:
        f.write(line)

def enable_live() -> dict:
    cfg = load_user_yaml()
    cfg.setdefault("live_trading", {})
    cfg["live_trading"]["enabled"] = True
    ok, msg = save_user_yaml(cfg)
    if ok:
        os.environ["CBP_LIVE_ARMED"] = "YES"
        armed, reason = live_enabled_and_armed()
        _log_audit("ENABLE_LIVE", True, reason)
        return {"ok": True, "armed": armed, "reason": reason, "msg": "Live enabled + armed"}
    _log_audit("ENABLE_LIVE", False, msg)
    return {"ok": False, "msg": msg}

def disable_live() -> dict:
    cfg = load_user_yaml()
    cfg["live_trading"]["enabled"] = False
    ok, msg = save_user_yaml(cfg)
    os.environ.pop("CBP_LIVE_ARMED", None)
    armed, reason = live_enabled_and_armed()
    _log_audit("DISABLE_LIVE", True, reason)
    return {"ok": True, "armed": armed, "reason": reason, "msg": "Live disabled"}
