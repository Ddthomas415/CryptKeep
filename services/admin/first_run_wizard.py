from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from services.admin.config_editor import load_user_yaml, save_user_yaml, ensure_user_yaml_exists
from services.admin.kill_switch import ensure_default as ensure_kill_default, get_state as kill_state, set_armed
from services.market_data.poller import build_required_pairs, fetch_tickers_once
from services.market_data.cache_audit import missing_pairs as cache_missing_pairs
from services.admin.preflight import run_preflight

SAFE_DEFAULTS = {
    "risk": {"enable_live": False, "allow_unknown_notional": False, "min_order_usd": 10.0, "max_position_usd": 250.0, "max_daily_loss_usd": 75.0, "max_trades_per_day": 15},
    "preflight": {"venues": ["binance","coinbase","gateio"], "symbols": ["BTC/USDT"], "time_tolerance_ms": 1500, "private_check": False},
    "market_data_poller": {"venue": "binance","symbols": ["BTC/USDT"], "interval_sec": 15.0, "include_symbols": True, "extra_pairs": []},
    "safety": {"auto_disable_live_on_start": True}
}

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def merge_defaults(cfg: dict, defaults: dict) -> dict:
    out = dict(cfg or {})
    for k, v in (defaults or {}).items():
        if isinstance(v, dict):
            cur = out.get(k)
            if not isinstance(cur, dict):
                out[k] = dict(v)
            else:
                nv = dict(cur)
                for kk, vv in v.items():
                    if kk not in nv:
                        nv[kk] = vv
                out[k] = nv
        else:
            if k not in out:
                out[k] = v
    return out

def compute_first_run_status() -> dict:
    ensure_user_yaml_exists()
    ensure_kill_default()
    cfg = load_user_yaml()
    ks = kill_state()

    md = cfg.get("market_data_poller") if isinstance(cfg.get("market_data_poller"), dict) else {}
    pf = cfg.get("preflight") if isinstance(cfg.get("preflight"), dict) else {}
    symbols = md.get("symbols") or pf.get("symbols") or ["BTC/USDT"]
    venue = str(md.get("venue") or "binance").lower().strip()
    req_pairs = build_required_pairs([str(s).strip() for s in symbols], include_symbols=True, extra_pairs=(md.get("extra_pairs") or []))
    audit = cache_missing_pairs(venue, req_pairs)

    return {
        "ts": _now(),
        "kill_switch": ks,
        "risk_enable_live": bool(cfg.get("risk", {}).get("enable_live", False)),
        "config_presence": {k: isinstance(cfg.get(k), dict) for k in ["risk","preflight","market_data_poller"]},
        "cache": {"venue": venue, "symbols": symbols, "required_pairs_count": len(req_pairs), "missing_pairs_count": int(audit.get("missing_count", 0) or 0), "missing_pairs": audit.get("missing", [])},
        "suggested_defaults": SAFE_DEFAULTS,
    }

def apply_safe_defaults(dry_run: bool = False) -> dict:
    ensure_user_yaml_exists()
    ensure_kill_default()
    cfg = load_user_yaml()
    merged = merge_defaults(cfg, SAFE_DEFAULTS)
    merged_risk = merged.get("risk") or {}
    merged_risk["enable_live"] = False
    merged["risk"] = merged_risk
    ks = set_armed(True, note="first_run_defaults")
    out = save_user_yaml(merged, create_backup=True, dry_run=dry_run)
    return {"ok": bool(out.get("ok")), "dry_run": dry_run, "save": out, "kill_switch": ks}

def run_preflight_now() -> dict:
    cfg = load_user_yaml()
    pf = cfg.get("preflight") or SAFE_DEFAULTS["preflight"]
    venues = pf.get("venues") or SAFE_DEFAULTS["preflight"]["venues"]
    symbols = pf.get("symbols") or SAFE_DEFAULTS["preflight"]["symbols"]
    tol = int(pf.get("time_tolerance_ms",1500) or 1500)
    do_priv = bool(pf.get("private_check", False))
    return asyncio.run(run_preflight(venues=[str(v).lower() for v in venues], symbols=[str(s) for s in symbols], time_tolerance_ms=tol, do_private_check=do_priv))

def populate_cache_now() -> dict:
    cfg = load_user_yaml()
    md = cfg.get("market_data_poller") or SAFE_DEFAULTS["market_data_poller"]
    pf = cfg.get("preflight") or SAFE_DEFAULTS["preflight"]
    venue = str(md.get("venue") or "binance").lower().strip()
    symbols = md.get("symbols") or pf.get("symbols") or ["BTC/USDT"]
    req_pairs = build_required_pairs([str(s).strip() for s in symbols], include_symbols=True, extra_pairs=(md.get("extra_pairs") or []))
    return asyncio.run(fetch_tickers_once(venue, req_pairs))
