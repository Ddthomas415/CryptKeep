from __future__ import annotations
from datetime import datetime, timezone
import logging
import os
from services.admin.kill_switch import get_state as get_kill, set_armed
from services.admin.system_guard import get_state as get_system_guard_state
from services.admin.system_guard import set_state as set_system_guard_state
from services.admin.config_editor import load_user_yaml, save_user_yaml
from services.execution.event_log import log_event
from services.execution.live_arming import is_live_enabled, set_live_armed_state, set_live_enabled
from services.run_context import run_id

_LOG = logging.getLogger(__name__)

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def status() -> dict:
    cfg = load_user_yaml()
    live_enabled = is_live_enabled(cfg)
    ks = get_kill()
    guard = get_system_guard_state(fail_closed=False)
    return {
        "ts": _now(),
        "run_id": run_id(),
        "live_enabled": live_enabled,
        "risk_enable_live": live_enabled,
        "kill_switch_armed": bool(ks.get("armed", True)),
        "kill_switch": ks,
        "system_guard": guard,
    }

def disable_live_now(note: str = "wizard_disable_live") -> dict:
    cfg = load_user_yaml()
    prev = status()
    new_cfg = set_live_enabled(cfg, False)
    ok, msg = save_user_yaml(new_cfg, dry_run=False)
    save_out = {"ok": ok, "message": msg}
    if not ok:
        return {"ok": False, "reason": "config_save_failed", "save": save_out, "prev": prev}
    os.environ.pop("CBP_EXECUTION_ARMED", None)
    os.environ.pop("CBP_LIVE_ENABLED", None)
    os.environ.pop("CBP_EXECUTION_LIVE_ENABLED", None)
    ks2 = set_armed(True, note=str(note))
    armed_state = set_live_armed_state(False, writer="live_disable_wizard", reason=str(note))
    guard = set_system_guard_state("HALTED", writer="live_disable_wizard", reason=str(note))
    try:
        log_event(
            "system",
            "GLOBAL",
            "live_disabled",
            ref_id=None,
            payload={
                "ts": _now(),
                "run_id": run_id(),
                "pre": prev,
                "post": {
                    "live_enabled": False,
                    "risk_enable_live": False,
                    "armed_state": armed_state,
                    "kill_switch": ks2,
                    "system_guard": guard,
                },
                "note": str(note),
            },
        )
    except Exception as e:
        _LOG.warning("live disable event log failed: %s: %s", type(e).__name__, e)
    return {
        "ok": True,
        "prev": prev,
        "post": status(),
        "save": save_out,
        "armed_state": armed_state,
        "kill_switch": ks2,
        "system_guard": guard,
    }
