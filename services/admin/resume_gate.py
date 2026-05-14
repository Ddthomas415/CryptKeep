from __future__ import annotations

import os
from typing import Any, Dict

from services.admin.config_editor import load_user_yaml, save_user_yaml
from services.admin.kill_switch import set_armed
from services.admin.system_guard import set_state as set_system_guard_state
from services.admin.live_guard import live_allowed
from services.execution.live_arming import is_live_enabled, set_live_armed_state, set_live_enabled


def _restore_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    ok, msg = save_user_yaml(dict(cfg or {}))
    return {"ok": bool(ok), "message": str(msg)}


def resume_if_safe(*, note: str = "resume_if_safe") -> Dict[str, Any]:
    """
    Restore RUNNING only when the live guard checks pass for a resumable state.
    Returns a structured status payload for dashboard callers.
    """
    cfg_before = dict(load_user_yaml() or {})
    config_changed = False
    config_save: dict[str, Any] | None = None
    if not is_live_enabled(cfg_before):
        cfg_enabled = set_live_enabled(cfg_before, True)
        ok, msg = save_user_yaml(cfg_enabled)
        config_save = {"ok": bool(ok), "message": str(msg), "live_enabled": True}
        if not ok:
            return {
                "ok": False,
                "resumed": False,
                "reason": "config_save_failed",
                "save": config_save,
            }
        config_changed = True

    allowed, reason, details = live_allowed(
        allow_kill_switch_armed=True,
        allow_system_guard_halted=True,
    )
    if not bool(allowed):
        restored = _restore_cfg(cfg_before) if config_changed else None
        out = {"ok": False, "resumed": False, "reason": str(reason), "details": dict(details or {})}
        if config_save is not None:
            out["save"] = config_save
        if restored is not None:
            out["config_restore"] = restored
        return out
    try:
        armed_state = set_live_armed_state(True, writer="resume_gate", reason=str(note))
    except Exception as exc:
        out = {
            "ok": False,
            "resumed": False,
            "reason": f"live_arm_restore_failed:{type(exc).__name__}",
            "details": dict(details or {}),
        }
        if config_save is not None:
            out["save"] = config_save
        if config_changed:
            out["config_restore"] = _restore_cfg(cfg_before)
        return out
    os.environ["CBP_EXECUTION_ARMED"] = "YES"
    try:
        kill_switch = set_armed(False, note=note)
        system_guard = set_system_guard_state("RUNNING", writer="resume_gate", reason=str(note))
    except Exception as exc:
        os.environ.pop("CBP_EXECUTION_ARMED", None)
        rollback_arm = set_live_armed_state(False, writer="resume_gate", reason=f"{note}:rollback_system_guard_failed")
        rollback = set_armed(True, note=f"{note}:rollback_system_guard_failed")
        out = {
            "ok": False,
            "resumed": False,
            "reason": f"system_guard_resume_failed:{type(exc).__name__}",
            "armed_state": rollback_arm,
            "kill_switch": rollback,
            "details": dict(details or {}),
        }
        if config_save is not None:
            out["save"] = config_save
        if config_changed:
            out["config_restore"] = _restore_cfg(cfg_before)
        return out
    out = {
        "ok": True,
        "resumed": True,
        "reason": "ok",
        "armed_state": armed_state,
        "kill_switch": kill_switch,
        "system_guard": system_guard,
        "details": dict(details or {}),
    }
    if config_save is not None:
        out["save"] = config_save
    return out
