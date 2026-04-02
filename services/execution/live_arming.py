from __future__ import annotations

import hashlib
import json
import os
import secrets
import time
from typing import Any

from services.admin.config_editor import load_user_yaml
from services.os.app_paths import data_dir


STATE_PATH = data_dir() / "live_arming.json"


def _load() -> dict:
    try:
        if STATE_PATH.exists():
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"version": 1, "active": None}


def _save(st: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(st, indent=2, sort_keys=True), encoding="utf-8")


def _sha256(s: str) -> str:
    return hashlib.sha256(str(s).encode("utf-8")).hexdigest()


def _truthy(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on", "y"}


def _bool_value(*values: Any, default: bool = False) -> bool:
    for value in values:
        if value is None:
            continue
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return _truthy(value)
        return bool(value)
    return bool(default)


def _float_value(*values: Any, default: float = 0.0) -> float:
    for value in values:
        if value is None:
            continue
        try:
            return float(value)
        except Exception:
            continue
    return float(default)


def _int_value(*values: Any, default: int = 0) -> int:
    for value in values:
        if value is None:
            continue
        try:
            return int(float(value))
        except Exception:
            continue
    return int(default)


def is_live_enabled(cfg: dict[str, Any] | None = None) -> bool:
    cfg = cfg if isinstance(cfg, dict) else load_user_yaml()

    execution = cfg.get("execution") if isinstance(cfg.get("execution"), dict) else {}
    canonical = execution.get("live_enabled")
    if canonical is not None:
        return _truthy(canonical)

    live = cfg.get("live") if isinstance(cfg.get("live"), dict) else {}
    live_trading = cfg.get("live_trading") if isinstance(cfg.get("live_trading"), dict) else {}
    risk = cfg.get("risk") if isinstance(cfg.get("risk"), dict) else {}

    fallback_candidates = (
        live.get("enabled"),
        live_trading.get("enabled"),
        risk.get("enable_live"),
    )
    return any(_truthy(v) for v in fallback_candidates)


def set_live_enabled(cfg: dict[str, Any] | None, enabled: bool) -> dict[str, Any]:
    out = dict(cfg or {})
    value = bool(enabled)

    live = dict(out.get("live") if isinstance(out.get("live"), dict) else {})
    live["enabled"] = value
    out["live"] = live

    live_trading = dict(out.get("live_trading") if isinstance(out.get("live_trading"), dict) else {})
    live_trading["enabled"] = value
    out["live_trading"] = live_trading

    risk = dict(out.get("risk") if isinstance(out.get("risk"), dict) else {})
    risk["enable_live"] = value
    out["risk"] = risk

    execution = dict(out.get("execution") if isinstance(out.get("execution"), dict) else {})
    execution["live_enabled"] = value
    out["execution"] = execution
    return out


def live_enabled_and_armed() -> tuple[bool, str]:
    cfg = load_user_yaml()
    if not is_live_enabled(cfg):
        return False, "live_disabled"

    armed_env = [
        ("CBP_EXECUTION_ARMED", os.environ.get("CBP_EXECUTION_ARMED")),
        ("CBP_LIVE_ARMED", os.environ.get("CBP_LIVE_ARMED")),
        ("CBP_LIVE_ENABLED", os.environ.get("CBP_LIVE_ENABLED")),
        ("ENABLE_LIVE_TRADING", os.environ.get("ENABLE_LIVE_TRADING")),
        ("LIVE_TRADING", os.environ.get("LIVE_TRADING")),
    ]
    for name, value in armed_env:
        if _truthy(value):
            return True, f"env:{name}"
    return False, "live_not_armed"


def live_risk_cfg() -> dict[str, float | int]:
    cfg = load_user_yaml()
    risk = cfg.get("risk") if isinstance(cfg.get("risk"), dict) else {}
    live = risk.get("live") if isinstance(risk.get("live"), dict) else {}
    return {
        "max_trades_per_day": _int_value(live.get("max_trades_per_day"), risk.get("max_trades_per_day"), default=0),
        "max_daily_notional_quote": _float_value(live.get("max_daily_notional_quote"), risk.get("max_daily_notional_quote"), default=0.0),
        "min_order_notional_quote": _float_value(
            live.get("min_order_notional_quote"),
            risk.get("min_order_notional_quote"),
            risk.get("min_order_usd"),
            default=0.0,
        ),
    }


def issue_token(*, ttl_minutes: int = 30) -> dict:
    token = secrets.token_urlsafe(18)
    now = time.time()
    exp = now + (int(ttl_minutes) * 60)
    st = _load()
    st["active"] = {"hash": _sha256(token), "issued_epoch": now, "expires_epoch": exp, "consumed": False}
    _save(st)
    return {"ok": True, "token": token, "expires_epoch": exp, "path": str(STATE_PATH)}


def status() -> dict:
    st = _load()
    a = st.get("active")
    if not isinstance(a, dict):
        return {"ok": True, "active": None, "path": str(STATE_PATH)}
    return {"ok": True, "active": a, "path": str(STATE_PATH)}


def verify_and_consume(token: str) -> dict:
    st = _load()
    a = st.get("active")
    if not isinstance(a, dict):
        return {"ok": False, "reason": "no_active_token"}
    if bool(a.get("consumed")):
        return {"ok": False, "reason": "token_already_consumed"}
    now = time.time()
    if now > float(a.get("expires_epoch") or 0):
        return {"ok": False, "reason": "token_expired"}
    if _sha256(token) != str(a.get("hash")):
        return {"ok": False, "reason": "token_mismatch"}
    a["consumed"] = True
    a["consumed_epoch"] = now
    st["active"] = a
    _save(st)
    return {"ok": True, "consumed": True}
