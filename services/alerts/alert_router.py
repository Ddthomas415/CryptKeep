from __future__ import annotations

from typing import Any, Dict

from services.alerts.alert_dispatcher import send_alert
from services.alerts.rate_limiter import allow

_LEVELS = {"info": 10, "warn": 20, "error": 30}

def _lvl(x: str) -> int:
    return _LEVELS.get((x or "error").strip().lower(), 30)

REDACT_KEYS = {
    "apikey","api_key","key",
    "secret","api_secret",
    "password","passphrase",
    "authorization","auth",
    "token","access_token","refresh_token",
    "slack_webhook_url",
}

def _looks_like_secret(s: str) -> bool:
    if not isinstance(s, str):
        return False
    ss = s.strip()
    if ss.startswith("https://hooks.slack.com/"):
        return True
    # very long strings are likely secrets/tokens
    return len(ss) >= 80

def redact(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            kk = str(k).strip().lower()
            if kk in REDACT_KEYS:
                out[k] = "<redacted>"
            else:
                out[k] = redact(v)
        return out
    if isinstance(obj, list):
        return [redact(x) for x in obj[:2000]]
    if isinstance(obj, str):
        return "<redacted>" if _looks_like_secret(obj) else obj
    return obj

def _cfg_alerts(cfg: dict) -> dict:
    a = cfg.get("alerts") if isinstance(cfg.get("alerts"), dict) else {}
    a.setdefault("enabled", False)
    a.setdefault("min_level", "error")
    a.setdefault("slack_webhook_url", "")
    a.setdefault("rate_limit_sec_default", 60)
    a.setdefault("never_alert_on_dry_run", True)  # safety default
    rules = a.get("rules") if isinstance(a.get("rules"), dict) else {}
    a["rules"] = rules
    return a

def _rule_for_stage(a: dict, stage: str) -> dict:
    rules = a.get("rules") if isinstance(a.get("rules"), dict) else {}
    r = rules.get(stage) if isinstance(rules.get(stage), dict) else {}
    out = {
        "enabled": bool(r.get("enabled", False)),
        "level": str(r.get("level", "error")).strip().lower(),
        "rate_limit_sec": int(r.get("rate_limit_sec", a.get("rate_limit_sec_default", 60))),
    }
    if out["level"] not in ("info", "warn", "error"):
        out["level"] = "error"
    if out["rate_limit_sec"] < 0:
        out["rate_limit_sec"] = 0
    return out

def route_order_event(*, cfg: dict, event: dict) -> dict:
    a = _cfg_alerts(cfg)
    if not bool(a.get("enabled", False)):
        return {"ok": True, "skipped": True, "reason": "alerts_disabled"}

    stage = str(event.get("stage") or "").strip()
    if not stage:
        return {"ok": True, "skipped": True, "reason": "missing_stage"}

    # hard safety: dry_run alerts disabled unless explicitly allowed
    if stage == "dry_run" and bool(a.get("never_alert_on_dry_run", True)):
        # If user explicitly enables dry_run rule, allow it.
        r0 = _rule_for_stage(a, "dry_run")
        if not bool(r0.get("enabled", False)):
            return {"ok": True, "skipped": True, "reason": "dry_run_suppressed_by_policy"}

    r = _rule_for_stage(a, stage)
    if not bool(r.get("enabled", False)):
        return {"ok": True, "skipped": True, "reason": "rule_disabled", "stage": stage}

    level = str(r.get("level", "error"))
    if _lvl(level) < _lvl(str(a.get("min_level", "error"))):
        return {"ok": True, "skipped": True, "reason": "below_min_level", "stage": stage, "level": level}

    venue = str(event.get("venue") or "")
    symbol = str(event.get("symbol") or "")
    key = f"order_event::{stage}::{venue}::{symbol}"
    rl = allow(key=key, min_interval_sec=int(r.get("rate_limit_sec", 60)))
    if not bool(rl.get("allowed", False)):
        return {"ok": True, "skipped": True, "reason": "rate_limited", "stage": stage, "rate_limit": rl}

    msg = f"Order event: {stage} ({venue} {symbol})"
    payload = redact({
        "stage": stage,
        "venue": venue,
        "symbol": symbol,
        "side": event.get("side"),
        "order_type": event.get("order_type"),
        "order_id": event.get("order_id"),
        "status": event.get("status"),
        "fills_n": event.get("fills_n"),
        "error": event.get("error"),
        "guard": event.get("guard"),
        "idempotency": event.get("idempotency"),
        "audit": event.get("audit"),
    })
    return send_alert(cfg=cfg, level=level, message=msg, payload=payload)

def test_alert(*, cfg: dict) -> dict:
    a = _cfg_alerts(cfg)
    if not bool(a.get("enabled", False)):
        return {"ok": False, "reason": "alerts_disabled_toggle_off"}
    return send_alert(cfg=cfg, level="info", message="CryptoBotPro test alert", payload={"kind": "test"})
