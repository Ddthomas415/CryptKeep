from __future__ import annotations

import os
from typing import Any, Dict

from services.admin.config_editor import load_user_yaml
from services.admin.kill_switch import set_armed
from services.admin.live_operator_audit import record_live_resume_event
from services.admin.system_guard import set_state as set_system_guard_state
from services.admin.live_guard import live_allowed
from services.execution.live_arming import (
    ceremony_resume_provenance,
    is_live_enabled,
    set_live_armed_state,
)


def resume_if_safe(*, note: str = "resume_if_safe") -> Dict[str, Any]:
    """
    Restore RUNNING only when a completed live-enable ceremony recently
    authorized live execution and the live guard checks pass.

    This gate never writes ``execution.live_enabled``. A cold/absent live
    config refuses with ``live_not_enabled_ceremony_required``; missing or
    expired ceremony provenance refuses with ``ceremony_provenance:*``. The
    operator recovery path for either refusal is the one-time-token live-enable
    ceremony in ``services.execution.live_enable``, not this resume gate.

    Returns a structured status payload for dashboard callers.
    """
    cfg_before = dict(load_user_yaml() or {})
    if not is_live_enabled(cfg_before):
        return {
            "ok": False,
            "resumed": False,
            "reason": "live_not_enabled_ceremony_required",
            "details": {"live_enabled": False},
        }

    provenance = dict(ceremony_resume_provenance() or {})
    if not bool(provenance.get("ok")):
        return {
            "ok": False,
            "resumed": False,
            "reason": f"ceremony_provenance:{provenance.get('reason')}",
            "provenance": provenance,
        }

    allowed, reason, details = live_allowed(
        allow_kill_switch_armed=True,
        allow_system_guard_halted=True,
    )
    if not bool(allowed):
        return {
            "ok": False,
            "resumed": False,
            "reason": str(reason),
            "details": dict(details or {}),
            "provenance": provenance,
        }
    try:
        armed_state = set_live_armed_state(True, writer="resume_gate", reason=str(note))
    except Exception as exc:
        return {
            "ok": False,
            "resumed": False,
            "reason": f"live_arm_restore_failed:{type(exc).__name__}",
            "details": dict(details or {}),
            "provenance": provenance,
        }
    os.environ["CBP_EXECUTION_ARMED"] = "YES"
    try:
        kill_switch = set_armed(False, note=note)
        system_guard = set_system_guard_state("RUNNING", writer="resume_gate", reason=str(note))
    except Exception as exc:
        os.environ.pop("CBP_EXECUTION_ARMED", None)
        rollback_arm = set_live_armed_state(False, writer="resume_gate", reason=f"{note}:rollback_system_guard_failed")
        rollback = set_armed(True, note=f"{note}:rollback_system_guard_failed")
        return {
            "ok": False,
            "resumed": False,
            "reason": f"system_guard_resume_failed:{type(exc).__name__}",
            "armed_state": rollback_arm,
            "kill_switch": rollback,
            "details": dict(details or {}),
            "provenance": provenance,
        }
    operator_event = record_live_resume_event(
        source="resume_gate",
        reason=str(note),
        result="ok",
        pre_state={
            "details": dict(details or {}),
            "provenance": provenance,
        },
        post_state={
            "armed_state": armed_state,
            "kill_switch": kill_switch,
            "system_guard": system_guard,
        },
        extra={"details": dict(details or {})},
    )
    if not bool(operator_event.get("ok")):
        os.environ.pop("CBP_EXECUTION_ARMED", None)
        rollback_arm = set_live_armed_state(
            False,
            writer="resume_gate",
            reason=f"{note}:rollback_operator_event_failed",
        )
        rollback_kill = set_armed(True, note=f"{note}:rollback_operator_event_failed")
        rollback_guard = set_system_guard_state(
            "HALTED",
            writer="resume_gate",
            reason=f"{note}:rollback_operator_event_failed",
        )
        return {
            "ok": False,
            "resumed": False,
            "reason": "operator_event_write_failed_live_resume_rolled_back",
            "operator_event": operator_event,
            "armed_state": rollback_arm,
            "kill_switch": rollback_kill,
            "system_guard": rollback_guard,
            "details": dict(details or {}),
            "provenance": provenance,
        }
    return {
        "ok": True,
        "resumed": True,
        "reason": "ok",
        "armed_state": armed_state,
        "kill_switch": kill_switch,
        "system_guard": system_guard,
        "details": dict(details or {}),
        "provenance": provenance,
        "operator_event": operator_event,
    }
