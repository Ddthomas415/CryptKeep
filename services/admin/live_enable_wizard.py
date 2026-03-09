from __future__ import annotations
import os
from datetime import datetime, timezone
from services.admin.config_editor import load_user_yaml, save_user_yaml
from services.execution.live_arming import live_enabled_and_armed, set_live_enabled
from services.os.app_paths import runtime_dir, ensure_dirs

ensure_dirs()
AUDIT_LOG = runtime_dir() / "logs" / "live_arm_audit.log"

def _log_audit(action: str, success: bool, reason: str = "") -> None:
    ts = datetime.now(timezone.utc).isoformat()
    line = f"{ts} | {action} | success={success} | reason={reason}\n"
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(line)

def enable_live() -> dict:
    cfg = set_live_enabled(load_user_yaml(), True)
    ok, msg = save_user_yaml(cfg)
    save = {"ok": ok, "message": msg}
    if not ok:
        _log_audit("ENABLE_LIVE", False, msg)
        return {"ok": False, "msg": msg, "save": save}

    os.environ["CBP_LIVE_ARMED"] = "YES"
    armed, reason = live_enabled_and_armed()
    _log_audit("ENABLE_LIVE", True, reason)
    return {"ok": True, "armed": armed, "reason": reason, "msg": "Live enabled + armed", "save": save}

def disable_live() -> dict:
    cfg = set_live_enabled(load_user_yaml(), False)
    ok, msg = save_user_yaml(cfg)
    save = {"ok": ok, "message": msg}
    if not ok:
        _log_audit("DISABLE_LIVE", False, msg)
        return {"ok": False, "msg": msg, "save": save}

    os.environ.pop("CBP_LIVE_ARMED", None)
    armed, reason = live_enabled_and_armed()
    _log_audit("DISABLE_LIVE", True, reason)
    return {"ok": True, "armed": armed, "reason": reason, "msg": "Live disabled", "save": save}
