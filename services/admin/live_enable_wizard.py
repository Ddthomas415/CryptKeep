from __future__ import annotations
import os
from datetime import datetime, timezone
from services.admin.config_editor import ConfigLoadError, load_user_yaml, save_user_yaml
from services.admin.system_guard import set_state as set_system_guard_state
from services.execution.live_arming import (
    live_enabled_and_armed,
    set_live_armed_state,
    set_live_enabled,
)
from services.admin.live_operator_audit import record_live_disable_event
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
    try:
        raw_cfg = load_user_yaml(strict=True)
    except ConfigLoadError as exc:
        msg = str(exc)
        _log_audit("ENABLE_LIVE", False, msg)
        return {"ok": False, "reason": "config_load_failed", "msg": msg}
    cfg = set_live_enabled(raw_cfg, True)
    ok, msg = save_user_yaml(cfg)
    save = {"ok": ok, "message": msg}
    if not ok:
        _log_audit("ENABLE_LIVE", False, msg)
        return {"ok": False, "msg": msg, "save": save}

    os.environ["CBP_EXECUTION_ARMED"] = "YES"
    armed_state = set_live_armed_state(True, writer="live_enable_wizard", reason="enable_live")
    armed, reason = live_enabled_and_armed()
    guard = None
    if armed:
        guard = set_system_guard_state("RUNNING", writer="live_enable_wizard", reason="enable_live")
    _log_audit("ENABLE_LIVE", True, reason)
    return {
        "ok": True,
        "armed": armed,
        "reason": reason,
        "msg": "Live enabled + armed",
        "save": save,
        "armed_state": armed_state,
        "system_guard": guard,
    }

def disable_live() -> dict:
    config_error = ""
    pre_state = {
        "env_execution_armed": os.environ.get("CBP_EXECUTION_ARMED"),
        "env_live_enabled": os.environ.get("CBP_LIVE_ENABLED"),
        "env_execution_live_enabled": os.environ.get("CBP_EXECUTION_LIVE_ENABLED"),
        "config_loaded": False,
        "live_enabled_before": None,
    }
    try:
        raw_cfg = load_user_yaml(strict=True)
    except ConfigLoadError as exc:
        config_error = str(exc)
        save = {
            "ok": False,
            "message": config_error,
            "reason": "config_load_failed",
            "skipped": True,
        }
    else:
        pre_state["config_loaded"] = True
        pre_state["live_enabled_before"] = bool((raw_cfg.get("execution") or {}).get("live_enabled"))
        cfg = set_live_enabled(raw_cfg, False)
        ok, msg = save_user_yaml(cfg)
        save = {"ok": ok, "message": msg}

    os.environ.pop("CBP_EXECUTION_ARMED", None)
    os.environ.pop("CBP_LIVE_ENABLED", None)
    os.environ.pop("CBP_EXECUTION_LIVE_ENABLED", None)
    armed_state = set_live_armed_state(False, writer="live_enable_wizard", reason="disable_live")
    armed, reason = live_enabled_and_armed()
    guard = set_system_guard_state("HALTED", writer="live_enable_wizard", reason="disable_live")
    out_reason = (
        "config_load_failed_runtime_halted"
        if config_error
        else ("config_save_failed_runtime_halted" if not bool(save.get("ok")) else reason)
    )
    _log_audit("DISABLE_LIVE", True, out_reason)
    operator_event = record_live_disable_event(
        source="live_enable_wizard",
        reason="disable_live",
        result=out_reason,
        pre_state=pre_state,
        post_state={
            "armed": armed,
            "armed_state": armed_state,
            "system_guard": guard,
            "save": save,
            "env_execution_armed": os.environ.get("CBP_EXECUTION_ARMED"),
            "env_live_enabled": os.environ.get("CBP_LIVE_ENABLED"),
            "env_execution_live_enabled": os.environ.get("CBP_EXECUTION_LIVE_ENABLED"),
        },
    )
    return {
        "ok": True,
        "reason": out_reason,
        "armed": armed,
        "msg": "Live disabled",
        "save": save,
        "armed_state": armed_state,
        "system_guard": guard,
        "operator_event": operator_event,
    }
