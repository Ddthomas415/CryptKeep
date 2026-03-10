from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from services.admin.config_editor import load_user_yaml, save_user_yaml, ensure_user_yaml_exists
from services.admin.kill_switch import ensure_default as ensure_kill_default, get_state as kill_state, set_armed
from services.market_data.poller import build_required_pairs, fetch_tickers_once
from services.admin.preflight import run_preflight
from services.execution.live_arming import is_live_enabled
from services.os.app_paths import runtime_dir
from services.setup.config_manager import guided_setup_summary
from services.setup.config_manager import apply_risk_preset

MARKET_DATA_SNAPSHOT = runtime_dir() / "snapshots" / "market_data_poller.latest.json"

def _run_async_safely(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    import threading

    box = {"result": None, "error": None}

    def _runner():
        try:
            box["result"] = asyncio.run(coro)
        except Exception as e:
            box["error"] = e

    t = threading.Thread(target=_runner, daemon=True)
    t.start()
    t.join()

    if box["error"] is not None:
        raise box["error"]
    return box["result"]


SAFE_DEFAULTS = {
    "risk": {"enable_live": False, "allow_unknown_notional": False, "min_order_usd": 10.0, "max_position_usd": 250.0, "max_daily_loss_usd": 75.0, "max_trades_per_day": 15},
    "preflight": {"venues": ["coinbase","gateio"], "symbols": ["BTC/USD"], "time_tolerance_ms": 1500, "private_check": False},
    "market_data_poller": {"venue": "coinbase","symbols": ["BTC/USD"], "interval_sec": 15.0, "include_symbols": True, "extra_pairs": []},
    "safety": {"auto_disable_live_on_start": True}
}

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> dict:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def _audit_cached_pairs(venue: str, required_pairs: list[str]) -> dict:
    snapshot = _read_json(MARKET_DATA_SNAPSHOT)
    snapshot_venue = str(snapshot.get("venue") or "").lower().strip()
    cached_pairs = []
    if snapshot_venue == str(venue).lower().strip():
        cached_pairs.extend(str(p).strip() for p in (snapshot.get("pairs") or []) if str(p).strip())
        for tick in snapshot.get("ticks") or []:
            if isinstance(tick, dict):
                sym = str(tick.get("symbol") or "").strip()
                if sym:
                    cached_pairs.append(sym)
    cached_set = set(cached_pairs)
    missing = [pair for pair in required_pairs if pair not in cached_set]
    return {
        "missing_count": len(missing),
        "missing": missing,
        "snapshot_path": str(MARKET_DATA_SNAPSHOT),
        "snapshot_present": MARKET_DATA_SNAPSHOT.exists(),
    }

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
    venue = str(md.get("venue") or "coinbase").lower().strip()
    req_pairs = build_required_pairs([str(s).strip() for s in symbols], include_symbols=True, extra_pairs=(md.get("extra_pairs") or []))
    audit = _audit_cached_pairs(venue, req_pairs)

    return {
        "ts": _now(),
        "kill_switch": ks,
        "live_enabled": is_live_enabled(cfg),
        "risk_enable_live": is_live_enabled(cfg),
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
    ks = kill_state()
    if not dry_run:
        ks = set_armed(True, note="first_run_defaults")
    ok, msg = save_user_yaml(merged, dry_run=dry_run)
    save = {"ok": ok, "message": msg}
    return {"ok": ok, "dry_run": dry_run, "save": save, "kill_switch": ks}

def run_preflight_now() -> dict:
    cfg = load_user_yaml()
    pf = cfg.get("preflight") or SAFE_DEFAULTS["preflight"]
    venues = pf.get("venues") or SAFE_DEFAULTS["preflight"]["venues"]
    symbols = pf.get("symbols") or SAFE_DEFAULTS["preflight"]["symbols"]
    tol = int(pf.get("time_tolerance_ms",1500) or 1500)
    do_priv = bool(pf.get("private_check", False))
    return _run_async_safely(run_preflight(venues=[str(v).lower() for v in venues], symbols=[str(s) for s in symbols], time_tolerance_ms=tol, do_private_check=do_priv))

def populate_cache_now() -> dict:
    cfg = load_user_yaml()
    md = cfg.get("market_data_poller") or SAFE_DEFAULTS["market_data_poller"]
    pf = cfg.get("preflight") or SAFE_DEFAULTS["preflight"]
    venue = str(md.get("venue") or "coinbase").lower().strip()
    symbols = md.get("symbols") or pf.get("symbols") or ["BTC/USDT"]
    req_pairs = build_required_pairs([str(s).strip() for s in symbols], include_symbols=True, extra_pairs=(md.get("extra_pairs") or []))
    return _run_async_safely(fetch_tickers_once(venue, req_pairs))

def guided_setup_review() -> dict:
    cfg = load_user_yaml()
    return guided_setup_summary(cfg)

def guided_setup_preflight_review() -> dict:
    return {
        "summary": guided_setup_review(),
        "preflight": run_preflight_now(),
    }

def guided_setup_apply(patch: dict | None = None) -> dict:
    cfg = load_user_yaml()
    cfg = merge_defaults(cfg, {})
    if patch:
        cfg = merge_defaults(patch, cfg)
    save_user_yaml(cfg)
    return {
        "summary": guided_setup_review(),
        "preflight": run_preflight_now(),
    }

def guided_setup_apply_preset(preset: str) -> dict:
    cfg = load_user_yaml()
    cfg = merge_defaults(cfg, {})
    cfg = apply_risk_preset(cfg, preset)
    save_user_yaml(cfg)
    return {
        "summary": guided_setup_review(),
        "preflight": run_preflight_now(),
    }

def guided_setup_state() -> dict:
    return {
        "summary": guided_setup_review(),
        "preflight": run_preflight_now(),
        "status": compute_first_run_status(),
    }

def guided_setup_apply_state(patch: dict | None = None) -> dict:
    guided_setup_apply(patch)
    return guided_setup_state()

