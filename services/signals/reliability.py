from __future__ import annotations
import math
import time
import uuid
from collections import defaultdict
from typing import Iterable
from services.market_data.symbol_router import normalize_symbol, normalize_venue
from services.backtest.signal_replay import fetch_ohlcv
from storage.signal_reliability_sqlite import SignalReliabilitySQLite

def _bps(x: float) -> float:
    return float(x) * 10000.0

def _safe_float(x, default=0.0):
    try:
        v = float(x)
        if not math.isfinite(v):
            return default
        return v
    except Exception:
        return default

def _actionable(a: str) -> bool:
    return str(a).lower().strip() in ("buy", "sell")

def _ts_to_ms(ts_any) -> int:
    try:
        v = float(ts_any)
        if v > 10_000_000_000: # already ms
            return int(v)
        return int(v * 1000.0)
    except Exception:
        return 0

def score_signals_against_ohlcv(
    *,
    ohlcv: list[list],
    signals: list[dict],
    horizon_candles: int,
    threshold_bps: float,
) -> dict:
    if not ohlcv:
        return {"ok": False, "reason": "no_ohlcv"}
    ts_list = [int(r[0]) for r in ohlcv]
    def next_idx(ts_ms: int) -> int:
        for i, t in enumerate(ts_list):
            if t >= ts_ms:
                return i
        return len(ts_list) - 1
    n_total = len(signals)
    n_scored = 0
    n_hit = 0
    rets = []
    thr = float(threshold_bps) / 10000.0
    for s in signals:
        act = str(s.get("action") or "").lower().strip()
        if act not in ("buy","sell"):
            continue
        ts_ms = _ts_to_ms(s.get("ts_ms") or s.get("ts") or 0)
        i = next_idx(ts_ms)
        j = i + int(horizon_candles)
        if i < 0 or j >= len(ohlcv):
            continue
        entry = _safe_float(ohlcv[i][1], 0.0) # open
        exitp = _safe_float(ohlcv[j][4], 0.0) # close
        if entry <= 0 or exitp <= 0:
            continue
        ret = (exitp / entry) - 1.0 # signed
        if act == "sell":
            ret = -ret # invert so "good" sells are positive
        hit = (ret >= thr)
        n_scored += 1
        n_hit += 1 if hit else 0
        rets.append(ret)
    if n_scored <= 0:
        return {"ok": True, "n_signals": n_total, "n_scored": 0, "hit_rate": 0.0, "avg_return_bps": 0.0, "avg_abs_return_bps": 0.0}
    hit_rate = n_hit / float(n_scored)
    avg_ret = sum(rets) / float(len(rets))
    avg_abs = sum(abs(x) for x in rets) / float(len(rets))
    return {
        "ok": True,
        "n_signals": n_total,
        "n_scored": n_scored,
        "hit_rate": float(hit_rate),
        "avg_return_bps": float(_bps(avg_ret)),
        "avg_abs_return_bps": float(_bps(avg_abs)),
    }

def compute_and_store_reliability(
    *,
    inbox_rows: list[dict],
    venue: str,
    timeframe: str,
    horizon_candles: int = 6,
    threshold_bps: float = 5.0,
    symbol: str | None = None,
) -> dict:
    v = normalize_venue(venue)
    tf = str(timeframe)
    hc = int(horizon_candles)
    thr = float(threshold_bps)
    rows = []
    for r in inbox_rows:
        if symbol and str(r.get("symbol")) != str(symbol):
            continue
        if not _actionable(r.get("action","")):
            continue
        rows.append(r)
    if not rows:
        return {"ok": True, "note": "no_actionable_signals"}
    groups = defaultdict(list)
    for r in rows:
        key = (str(r.get("source") or ""), str(r.get("author") or ""), normalize_symbol(str(r.get("symbol") or "")))
        groups[key].append(r)
    sym_to_ohlcv = {}
    for (_, _, sym) in set((k[0], k[1], k[2]) for k in groups.keys()):
        try:
            sym_to_ohlcv[sym] = fetch_ohlcv(v, sym, timeframe=tf, limit=2000)
        except Exception as e:
            sym_to_ohlcv[sym] = []
    db = SignalReliabilitySQLite()
    stored = 0
    details = []
    for (src, author, sym), sigs in groups.items():
        sc = score_signals_against_ohlcv(
            ohlcv=sym_to_ohlcv.get(sym) or [],
            signals=sigs,
            horizon_candles=hc,
            threshold_bps=thr,
        )
        row = {
            "id": str(uuid.uuid4()),
            "source": src or "unknown",
            "author": author or "unknown",
            "symbol": sym,
            "venue": v,
            "timeframe": tf,
            "horizon_candles": hc,
            "threshold_bps": thr,
            "n_signals": int(sc.get("n_signals") or len(sigs)),
            "n_scored": int(sc.get("n_scored") or 0),
            "hit_rate": float(sc.get("hit_rate") or 0.0),
            "avg_return_bps": float(sc.get("avg_return_bps") or 0.0),
            "avg_abs_return_bps": float(sc.get("avg_abs_return_bps") or 0.0),
            "notes": "",
        }
        db.upsert(row)
        stored += 1
        details.append(row)
    return {"ok": True, "stored": stored, "venue": v, "timeframe": tf, "horizon_candles": hc, "threshold_bps": thr, "rows": details[:30]}
