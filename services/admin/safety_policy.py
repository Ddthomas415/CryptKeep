from __future__ import annotations

from typing import Any, Dict, List, Tuple

from services.admin.config_editor import load_user_yaml


DEFAULT_POLICY: Dict[str, Any] = {
    "kill_switch_required_for_live": True,
    "require_explicit_live_arming": True,
    "max_daily_loss_usd": 0.0,
    "max_trades_per_day": 0,
    "max_notional_per_trade_usd": 0.0,
    "notes": "",
}


def read_policy() -> Dict[str, Any]:
    cfg = load_user_yaml()
    safety = cfg.get("safety_policy") if isinstance(cfg.get("safety_policy"), dict) else {}
    out = dict(DEFAULT_POLICY)
    out.update({k: v for k, v in safety.items() if k in out})
    return out


def validate_policy(policy: Dict[str, Any] | None = None) -> Tuple[bool, List[str]]:
    p = dict(policy or read_policy())
    errors: list[str] = []
    if not isinstance(p.get("kill_switch_required_for_live"), bool):
        errors.append("kill_switch_required_for_live must be bool")
    if not isinstance(p.get("require_explicit_live_arming"), bool):
        errors.append("require_explicit_live_arming must be bool")
    for k in ("max_daily_loss_usd", "max_notional_per_trade_usd"):
        try:
            v = float(p.get(k) or 0.0)
            if v < 0:
                errors.append(f"{k} must be >= 0")
        except Exception:
            errors.append(f"{k} must be float")
    try:
        v = int(p.get("max_trades_per_day") or 0)
        if v < 0:
            errors.append("max_trades_per_day must be >= 0")
    except Exception:
        errors.append("max_trades_per_day must be int")
    return len(errors) == 0, errors
