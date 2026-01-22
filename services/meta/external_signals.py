from __future__ import annotations
import time
from collections import defaultdict
from services.admin.config_editor import load_user_yaml
from services.market_data.symbol_router import normalize_symbol, normalize_venue
from storage.signal_inbox_sqlite import SignalInboxSQLite

def _cfg() -> dict:
    cfg = load_user_yaml()
    m = cfg.get("meta_strategy") if isinstance(cfg.get("meta_strategy"), dict) else {}
    e = m.get("external") if isinstance(m.get("external"), dict) else {}
    return {
        "lookback_sec": int(e.get("lookback_sec", 6 * 3600) or 6 * 3600),
        "use_reliability": bool(e.get("use_reliability", True)),
        "fallback_weight": float(e.get("fallback_weight", 0.5) or 0.5),
        "min_confidence": float(e.get("min_confidence", 0.0) or 0.0),
    }

def _vote(action: str) -> int:
    a = str(action).lower().strip()
    if a == "buy": return 1
    if a == "sell": return -1
    return 0

def aggregate_external(symbol: str, *, venue: str, timeframe: str, horizon_candles: int) -> dict:
    cfg = _cfg()
    sym = normalize_symbol(symbol)
    rows = SignalInboxSQLite().list_signals(limit=2000, status=None, symbol=sym)
    now = time.time()
    lb = float(cfg["lookback_sec"])
    recent = []
    for r in rows:
        try:
            ts = float(r.get("ts") or 0.0)
            if ts > 10_000_000_000:
                ts = ts / 1000.0
        except Exception:
            ts = 0.0
        if now - ts <= lb:
            if float(r.get("confidence") or 0.0) >= float(cfg["min_confidence"]):
                recent.append(r)
    if not recent:
        return {"ok": True, "action": "hold", "score": 0.0, "confidence": 0.0, "n": 0, "used_reliability": False}
    used_rel = False
    rel_map = {}
    if cfg["use_reliability"]:
        try:
            from storage.signal_reliability_sqlite import SignalReliabilitySQLite
            rdb = SignalReliabilitySQLite()
            for r in recent:
                k = (str(r.get("source") or "unknown"), str(r.get("author") or "unknown"))
                if k in rel_map:
                    continue
                rel = rdb.get_one(
                    source=k[0],
                    author=k[1],
                    symbol=sym,
                    venue=normalize_venue(venue),
                    timeframe=str(timeframe),
                    horizon_candles=int(horizon_candles),
                )
                if rel and int(rel.get("n_scored") or 0) > 0:
                    rel_map[k] = float(rel.get("hit_rate") or 0.0)
                    used_rel = True
        except Exception:
            pass
    num = 0.0
    den = 0.0
    for r in recent:
        v = _vote(r.get("action"))
        if v == 0:
            continue
        w = rel_map.get((str(r.get("source") or "unknown"), str(r.get("author") or "unknown")), float(cfg["fallback_weight"]))
        w = max(0.0, min(1.0, float(w)))
        num += w * float(v)
        den += w
    if den <= 1e-9:
        return {"ok": True, "action": "hold", "score": 0.0, "confidence": 0.0, "n": len(recent), "used_reliability": used_rel}
    score = num / den # [-1..1]
    action = "hold"
    if score > 0.0: action = "buy"
    if score < 0.0: action = "sell"
    confidence = min(1.0, abs(score))
    return {"ok": True, "action": action, "score": float(score), "confidence": float(confidence), "n": len(recent), "used_reliability": used_rel}
