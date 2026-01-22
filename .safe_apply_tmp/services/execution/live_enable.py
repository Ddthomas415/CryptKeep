from __future__ import annotations
from services.admin.config_editor import load_user_yaml, save_user_yaml
from services.execution.live_arming import verify_and_consume
from services.execution.live_preflight import run_preflight
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
    if not pre.get("ok"):
        return {"ok": False, "reason": "preflight_failed", "preflight": pre}
    tok = verify_and_consume(token)
    if not tok.get("ok"):
        return {"ok": False, "reason": "token_failed", "token": tok, "preflight": pre}
    cfg = load_user_yaml()
    cfg.setdefault("live_trading", {})["dry_run"] = False
    save = save_user_yaml(cfg)
    return {"ok": True, "changed": {"live_trading.dry_run": False}, "save": save, "preflight": pre}
