from __future__ import annotations
from services.admin.config_editor import load_user_yaml, save_user_yaml
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
    cfg = set_live_enabled(load_user_yaml(), True)
    ok, msg = save_user_yaml(cfg)
    save = {"ok": ok, "message": msg}
    if not ok:
        return {"ok": False, "reason": "config_save_failed", "save": save, "preflight": preflight}
    armed_state = set_live_armed_state(True, writer="execution_live_enable", reason="token_enable_live")
    return {
        "ok": True,
        "changed": {
            "execution.live_enabled": True,
        },
        "armed_state": armed_state,
        "save": save,
        "preflight": preflight,
    }
