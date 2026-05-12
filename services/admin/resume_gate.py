from __future__ import annotations

import os
from typing import Any, Dict

from services.admin.config_editor import load_user_yaml, save_user_yaml
from services.admin.kill_switch import set_armed
from services.admin.system_guard import set_state as set_system_guard_state
from services.admin.live_guard import live_allowed
from services.execution.live_arming import set_live_armed_state, set_live_enabled


def resume_if_safe(*, note: str = "resume_if_safe") -> Dict[str, Any]:
    """
    Restore RUNNING only when the live guard checks pass for a resumable state.
    Returns a structured status payload for dashboard callers.

    Fix H5 (Drill 6): also writes live_enabled: true to the config so that
    live_enabled_and_armed() passes after a supervised restart.  Without this
    write, the arming signal was set but is_live_enabled(cfg) still returned
    False because resume_if_safe never updated the YAML.
    """
    allowed, reason, details = live_allowed(
        allow_kill_switch_armed=True,
        allow_system_guard_halted=True,
    )
    if not bool(allowed):
        return {"ok": False, "resumed": False, "reason": str(reason), "details": dict(details or {})}
    try:
        armed_state = set_live_armed_state(True, writer="resume_gate", reason=str(note))
    except Exception as exc:
        return {
            "ok": False,
            "resumed": False,
            "reason": f"live_arm_restore_failed:{type(exc).__name__}",
            "details": dict(details or {}),
        }
    # H5 fix: persist live_enabled: true so live_enabled_and_armed() passes
    # after a restart where this process's env var is no longer inherited.
    try:
        _cfg = load_user_yaml()
        _updated = set_live_enabled(_cfg, True)
        _saved, _save_err = save_user_yaml(_updated)
        if not _saved:
            details = dict(details or {})
            details["live_enabled_config_save_warning"] = _save_err
    except Exception as _cfg_exc:
        details = dict(details or {})
        details["live_enabled_config_save_warning"] = f"{type(_cfg_exc).__name__}:{_cfg_exc}"
    os.environ["CBP_EXECUTION_ARMED"] = "YES"
    kill_switch = set_armed(False, note=note)
    try:
        system_guard = set_system_guard_state("RUNNING", writer="resume_gate", reason=str(note))
    except Exception as exc:
        os.environ.pop("CBP_EXECUTION_ARMED", None)
        rollback_arm = set_live_armed_state(False, writer="resume_gate", reason=f"{note}:rollback_system_guard_failed")
        rollback = set_armed(True, note=f"{note}:rollback_system_guard_failed")
        # Also rollback live_enabled in config
        try:
            _rb_cfg = load_user_yaml()
            save_user_yaml(set_live_enabled(_rb_cfg, False))
        except Exception:
            pass
        return {
            "ok": False,
            "resumed": False,
            "reason": f"system_guard_resume_failed:{type(exc).__name__}",
            "armed_state": rollback_arm,
            "kill_switch": rollback,
            "details": dict(details or {}),
        }
    return {
        "ok": True,
        "resumed": True,
        "reason": "ok",
        "armed_state": armed_state,
        "kill_switch": kill_switch,
        "system_guard": system_guard,
        "details": dict(details or {}),
    }
