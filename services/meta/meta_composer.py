from __future__ import annotations
from services.markets.symbols import env_symbol
import os
import uuid
from services.admin.config_editor import load_user_yaml
from services.market_data.symbol_router import normalize_symbol, normalize_venue
from services.meta.internal_ema import ema_crossover_signal
from services.meta.external_signals import aggregate_external

def _cfg() -> dict:
    cfg = load_user_yaml()
    m = cfg.get("meta_strategy") if isinstance(cfg.get("meta_strategy"), dict) else {}
    i = m.get("internal") if isinstance(m.get("internal"), dict) else {}
    e = m.get("external") if isinstance(m.get("external"), dict) else {}
    c = m.get("compose") if isinstance(m.get("compose"), dict) else {}
    r = m.get("routing") if isinstance(m.get("routing"), dict) else {}
    return {
        "enabled": bool(m.get("enabled", False)),
        "venue": normalize_venue(str(os.environ.get("CBP_VENUE") or m.get("venue") or "coinbase")),
        "timeframe": str(m.get("timeframe", "1h") or "1h"),
        "horizon_candles": int(m.get("horizon_candles", 6) or 6),
        "internal": {
            "enabled": bool(i.get("enabled", True)),
            "weight": float(i.get("weight", 0.6) or 0.6),
            "ema_fast": int(i.get("ema_fast", 12) or 12),
            "ema_slow": int(i.get("ema_slow", 26) or 26),
        },
        "external": {
            "enabled": bool(e.get("enabled", True)),
            "weight": float(e.get("weight", 0.4) or 0.4),
        },
        "compose": {
            "decision_threshold": float(c.get("decision_threshold", 0.25) or 0.25),
            "conflict_hold": bool(c.get("conflict_hold", True)),
            "conflict_strong_threshold": float(c.get("conflict_strong_threshold", 0.60) or 0.60),
        },
        "routing": {
            "paper_enabled": bool(r.get("paper_enabled", False)),
            "base_qty": float(r.get("base_qty", 0.001) or 0.001),
            "qty_scale_by_score": bool(r.get("qty_scale_by_score", True)),
            "min_qty_scale": float(r.get("min_qty_scale", 0.5) or 0.5),
            "max_qty_scale": float(r.get("max_qty_scale", 1.5) or 1.5),
            "cooldown_sec": int(r.get("cooldown_sec", 300) or 300),
        }
    }

def compose(symbol: str) -> dict:
    cfg = _cfg()
    sym = normalize_symbol(symbol)
    venue = cfg["venue"]
    tf = cfg["timeframe"]
    hc = cfg["horizon_candles"]
    internal = {"ok": True, "action": "hold", "score": 0.0, "confidence": 0.0}
    external = {"ok": True, "action": "hold", "score": 0.0, "confidence": 0.0, "n": 0}
    if cfg["internal"]["enabled"]:
        internal = ema_crossover_signal(
            venue=venue, symbol=sym, timeframe=tf,
            fast=cfg["internal"]["ema_fast"], slow=cfg["internal"]["ema_slow"],
            limit=400,
        )
    if cfg["external"]["enabled"]:
        external = aggregate_external(sym, venue=venue, timeframe=tf, horizon_candles=hc)
    wi = float(cfg["internal"]["weight"]) if cfg["internal"]["enabled"] else 0.0
    we = float(cfg["external"]["weight"]) if cfg["external"]["enabled"] else 0.0
    den = max(1e-9, wi + we)
    si = float(internal.get("score") or 0.0)
    se = float(external.get("score") or 0.0)
    score = (wi * si + we * se) / den
    if cfg["compose"]["conflict_hold"]:
        thr = float(cfg["compose"]["conflict_strong_threshold"])
        if (si > thr and se < -thr) or (si < -thr and se > thr):
            return {
                "ok": True,
                "decision_id": str(uuid.uuid4()),
                "symbol": sym,
                "venue": venue,
                "timeframe": tf,
                "action": "hold",
                "score": 0.0,
                "confidence": 0.0,
                "internal": internal,
                "external": external,
                "reason": "conflict_hold",
            }
    dt = float(cfg["compose"]["decision_threshold"])
    action = "hold"
    if score >= dt: action = "buy"
    elif score <= -dt: action = "sell"
    confidence = min(1.0, abs(score))
    return {
        "ok": True,
        "decision_id": str(uuid.uuid4()),
        "symbol": sym,
        "venue": venue,
        "timeframe": tf,
        "action": action,
        "score": float(score),
        "confidence": float(confidence),
        "internal": internal,
        "external": external,
        "reason": "threshold",
    }

def routing_cfg() -> dict:
    return _cfg()["routing"]
