from __future__ import annotations
from services.admin.config_editor import ConfigLoadError, load_user_yaml, save_user_yaml
from services.admin.live_operator_audit import record_live_enable_event
from services.execution.live_arming import set_live_armed_state, set_live_enabled, verify_and_consume
from services.preflight.preflight import run_preflight


def _serialize_preflight_result(pre) -> dict:
    return {"ok": bool(getattr(pre, "ok", False)), "checks": list(getattr(pre, "checks", []) or [])}


def enable_live(*, token: str, checklist: dict) -> dict:
    required = [
        "i_understand_live_risk",
        "api_keys_configured",
        "risk_limits_set",
        "dry_run_tested",
        "i_accept_no_guarantees",
    ]
    missing = [k for k in required if not bool((checklist or {}).get(k))]
    if missing:
        return {"ok": False, "reason": "checklist_incomplete", "missing": missing}
    pre = run_preflight()
    preflight = _serialize_preflight_result(pre)
    if not preflight["ok"]:
        return {"ok": False, "reason": "preflight_failed", "preflight": preflight}
    tok = verify_and_consume(token)
    if not tok.get("ok"):
        return {"ok": False, "reason": "token_failed", "token": tok, "preflight": preflight}
    try:
        raw_cfg = load_user_yaml(strict=True)
    except ConfigLoadError as exc:
        return {
            "ok": False,
            "reason": "config_load_failed",
            "error": str(exc),
            "token": tok,
            "preflight": preflight,
        }
    pre_state = {
        "live_enabled_before": bool((raw_cfg.get("execution") or {}).get("live_enabled")),
        "token_consumed": bool(tok.get("ok")),
    }
    cfg = set_live_enabled(raw_cfg, True)
    ok, msg = save_user_yaml(cfg)
    save = {"ok": ok, "message": msg}
    if not ok:
        return {"ok": False, "reason": "config_save_failed", "save": save, "preflight": preflight}
    armed_state = set_live_armed_state(True, writer="execution_live_enable", reason="token_enable_live")
    operator_event = record_live_enable_event(
        source="execution_live_enable",
        reason="token_enable_live",
        result="ok",
        pre_state=pre_state,
        post_state={
            "changed": {"execution.live_enabled": True},
            "armed_state": armed_state,
            "save": save,
        },
        extra={"preflight": preflight},
    )
    if not bool(operator_event.get("ok")):
        rollback_save_ok, rollback_save_msg = save_user_yaml(raw_cfg)
        rollback_arm = set_live_armed_state(
            False,
            writer="execution_live_enable",
            reason="token_enable_live:rollback_operator_event_failed",
        )
        return {
            "ok": False,
            "reason": "operator_event_write_failed_live_enable_rolled_back",
            "operator_event": operator_event,
            "rollback": {
                "save": {"ok": rollback_save_ok, "message": rollback_save_msg},
                "armed_state": rollback_arm,
            },
            "preflight": preflight,
        }
    return {
        "ok": True,
        "changed": {
            "execution.live_enabled": True,
        },
        "armed_state": armed_state,
        "save": save,
        "preflight": preflight,
        "operator_event": operator_event,
    }
