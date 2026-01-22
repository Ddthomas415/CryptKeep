# apply_phase125.py - Phase 125: Reliability scoring + store + dashboard + optional paper weighting + config + checkpoints
from pathlib import Path

def write(path: str, content: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.lstrip("\n"), encoding="utf-8")
    print(f"Written/Updated: {path}")

def patch(path: str, fn):
    p = Path(path)
    if not p.exists():
        print(f"Skipping patch - file missing: {path}")
        return
    t = p.read_text(encoding="utf-8")
    nt = fn(t)
    if nt != t:
        p.write_text(nt, encoding="utf-8")
        print(f"Patched: {path}")
    else:
        print(f"No changes needed: {path}")

# 1) Reliability store (SQLite)
write("storage/signal_reliability_sqlite.py", r'''from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from services.os.app_paths import data_dir

DB_PATH = data_dir() / "signal_reliability.sqlite"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS signal_reliability (
  id TEXT PRIMARY KEY,
  updated_ts TEXT NOT NULL,
  source TEXT NOT NULL,
  author TEXT NOT NULL,
  symbol TEXT NOT NULL,
  venue TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  horizon_candles INTEGER NOT NULL,
  threshold_bps REAL NOT NULL,
  n_signals INTEGER NOT NULL,
  n_scored INTEGER NOT NULL,
  hit_rate REAL NOT NULL,
  avg_return_bps REAL NOT NULL,
  avg_abs_return_bps REAL NOT NULL,
  notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_sr_key ON signal_reliability(source, author, symbol, venue, timeframe, horizon_candles);
CREATE INDEX IF NOT EXISTS idx_sr_updated ON signal_reliability(updated_ts);
"""

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, isolation_level=None, check_same_thread=False)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    for stmt in SCHEMA.strip().split(";"):
        s = stmt.strip()
        if s:
            con.execute(s)
    return con

class SignalReliabilitySQLite:
    def __init__(self) -> None:
        _connect().close()

    def upsert(self, row: Dict[str, Any]) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO signal_reliability("
                "id, updated_ts, source, author, symbol, venue, timeframe, horizon_candles, threshold_bps,"
                "n_signals, n_scored, hit_rate, avg_return_bps, avg_abs_return_bps, notes"
                ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    str(row["id"]),
                    str(row.get("updated_ts") or _now()),
                    str(row["source"]),
                    str(row["author"]),
                    str(row["symbol"]),
                    str(row["venue"]),
                    str(row["timeframe"]),
                    int(row["horizon_candles"]),
                    float(row["threshold_bps"]),
                    int(row["n_signals"]),
                    int(row["n_scored"]),
                    float(row["hit_rate"]),
                    float(row["avg_return_bps"]),
                    float(row["avg_abs_return_bps"]),
                    str(row.get("notes") or ""),
                ),
            )
        finally:
            con.close()

    def list(self, limit: int = 500, symbol: str | None = None) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            q = ("SELECT id, updated_ts, source, author, symbol, venue, timeframe, horizon_candles, threshold_bps, "
                 "n_signals, n_scored, hit_rate, avg_return_bps, avg_abs_return_bps, notes "
                 "FROM signal_reliability")
            args = []
            if symbol:
                q += " WHERE symbol=?"
                args.append(str(symbol))
            q += " ORDER BY updated_ts DESC LIMIT ?"
            args.append(int(limit))
            rows = con.execute(q, tuple(args)).fetchall()
            return [
                {
                    "id": r[0], "updated_ts": r[1], "source": r[2], "author": r[3], "symbol": r[4],
                    "venue": r[5], "timeframe": r[6], "horizon_candles": r[7], "threshold_bps": r[8],
                    "n_signals": r[9], "n_scored": r[10], "hit_rate": r[11], "avg_return_bps": r[12],
                    "avg_abs_return_bps": r[13], "notes": r[14],
                }
                for r in rows
            ]
        finally:
            con.close()

    def get_one(self, *, source: str, author: str, symbol: str, venue: str, timeframe: str, horizon_candles: int) -> Dict[str, Any] | None:
        con = _connect()
        try:
            r = con.execute(
                "SELECT id, updated_ts, source, author, symbol, venue, timeframe, horizon_candles, threshold_bps, "
                "n_signals, n_scored, hit_rate, avg_return_bps, avg_abs_return_bps, notes "
                "FROM signal_reliability WHERE source=? AND author=? AND symbol=? AND venue=? AND timeframe=? AND horizon_candles=? "
                "ORDER BY updated_ts DESC LIMIT 1",
                (str(source), str(author), str(symbol), str(venue), str(timeframe), int(horizon_candles)),
            ).fetchone()
            if not r:
                return None
            return {
                "id": r[0], "updated_ts": r[1], "source": r[2], "author": r[3], "symbol": r[4],
                "venue": r[5], "timeframe": r[6], "horizon_candles": r[7], "threshold_bps": r[8],
                "n_signals": r[9], "n_scored": r[10], "hit_rate": r[11], "avg_return_bps": r[12],
                "avg_abs_return_bps": r[13], "notes": r[14],
            }
        finally:
            con.close()
''')

# 2) Reliability scoring logic
write("services/signals/reliability.py", r'''from __future__ import annotations
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
''')

# 3) CLI recompute script
write("scripts/recompute_signal_reliability.py", r'''#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from storage.signal_inbox_sqlite import SignalInboxSQLite
from services.signals.reliability import compute_and_store_reliability

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--venue", default="binance")
    ap.add_argument("--timeframe", default="1h")
    ap.add_argument("--horizon", type=int, default=6)
    ap.add_argument("--threshold-bps", type=float, default=5.0)
    ap.add_argument("--symbol", default=None)
    args = ap.parse_args()
    inbox = SignalInboxSQLite()
    rows = inbox.list_signals(limit=5000, status=None, symbol=args.symbol)
    res = compute_and_store_reliability(
        inbox_rows=rows,
        venue=args.venue,
        timeframe=args.timeframe,
        horizon_candles=int(args.horizon),
        threshold_bps=float(args.threshold_bps),
        symbol=(args.symbol.strip() or None),
    )
    print(json.dumps(res, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
''')

# 4) Optional: use reliability in PAPER routing (OFF by default)
def patch_routing(t: str) -> str:
    if "signals_learning" in t and "SignalReliabilitySQLite" in t:
        return t
    if "from storage.signal_reliability_sqlite import SignalReliabilitySQLite" not in t:
        t = t.replace(
            "from storage.intent_queue_sqlite import IntentQueueSQLite\n",
            "from storage.intent_queue_sqlite import IntentQueueSQLite\nfrom storage.signal_reliability_sqlite import SignalReliabilitySQLite\n",
            1
        )
    if "signals_learning" not in t:
        t = t.replace(
            ' return {\n "auto_route_to_paper": bool(r.get("auto_route_to_paper", False)),\n',
            ' sl = cfg.get("signals_learning") if isinstance(cfg.get("signals_learning"), dict) else {}\n'
            ' return {\n "auto_route_to_paper": bool(r.get("auto_route_to_paper", False)),\n'
            ' "signals_learning": {\n'
            ' "enabled": bool(sl.get("enabled", False)),\n'
            ' "min_n_scored": int(sl.get("min_n_scored", 20) or 20),\n'
            ' "min_hit_rate": float(sl.get("min_hit_rate", 0.55) or 0.55),\n'
            ' "horizon_candles": int(sl.get("horizon_candles", 6) or 6),\n'
            ' "timeframe": str(sl.get("timeframe", "1h") or "1h"),\n'
            ' "venue": normalize_venue(str(sl.get("venue", "binance") or "binance")),\n'
            ' "scale_qty": bool(sl.get("scale_qty", False)),\n'
            ' "qty_scale_min": float(sl.get("qty_scale_min", 0.5) or 0.5),\n'
            ' "qty_scale_max": float(sl.get("qty_scale_max", 1.5) or 1.5),\n'
            ' },\n',
            1
        )
    marker = " venue = normalize_venue(str(sig.get(\"venue_hint\") or cfg[\"default_venue\"]))\n qty = float(sig.get(\"qty\") or cfg[\"default_qty\"])"
    if marker in t:
        t = t.replace(
            marker,
            marker +
            "\n\n # Optional learning gate (OFF by default)\n"
            " sl = cfg.get('signals_learning') or {}\n"
            " if bool(sl.get('enabled')):\n"
            "     try:\n"
            "         sdb = SignalReliabilitySQLite()\n"
            "         rel = sdb.get_one(\n"
            "             source=source or 'unknown',\n"
            "             author=author or 'unknown',\n"
            "             symbol=symbol,\n"
            "             venue=str(sl.get('venue') or venue),\n"
            "             timeframe=str(sl.get('timeframe') or '1h'),\n"
            "             horizon_candles=int(sl.get('horizon_candles') or 6),\n"
            "         )\n"
            "         if rel and int(rel.get('n_scored') or 0) >= int(sl.get('min_n_scored') or 20):\n"
            "             hr = float(rel.get('hit_rate') or 0.0)\n"
            "             if hr < float(sl.get('min_hit_rate') or 0.55):\n"
            "                 return {'ok': False, 'reason': 'learning:hit_rate_below_min', 'hit_rate': hr, 'min_hit_rate': float(sl.get('min_hit_rate') or 0.55)}\n"
            "             if bool(sl.get('scale_qty')):\n"
            "                 base = float(sl.get('min_hit_rate') or 0.55)\n"
            "                 x = 0.0 if hr <= base else min(1.0, (hr - base) / max(1e-9, 1.0 - base))\n"
            "                 qmin = float(sl.get('qty_scale_min') or 0.5)\n"
            "                 qmax = float(sl.get('qty_scale_max') or 1.5)\n"
            "                 scale = qmin + (qmax - qmin) * x\n"
            "                 qty = float(qty) * float(scale)\n"
            "     except Exception:\n"
            "         pass\n"
        )
    return t

patch("services/signals/routing.py", patch_routing)

# 5) Dashboard panel: compute reliability + leaderboard
def patch_dashboard(t: str) -> str:
    if "Signal Learning v1 (Reliability Scoring)" in t:
        return t
    add = r'''
st.divider()
st.header("Signal Learning v1 (Reliability Scoring)")
st.caption("Scores public signals per (source, author, symbol) using OHLCV replay: entry next open → exit horizon close. Stores hit_rate + avg_return_bps. Used for PAPER routing only if enabled.")
try:
    import pandas as pd
    from storage.signal_inbox_sqlite import SignalInboxSQLite
    from storage.signal_reliability_sqlite import SignalReliabilitySQLite
    from services.signals.reliability import compute_and_store_reliability
    from services.admin.config_editor import load_user_yaml
    cfg = load_user_yaml()
    venues = (cfg.get("preflight", {}).get("venues") if isinstance(cfg.get("preflight"), dict) else None) or ["binance","coinbase","gateio"]
    tf = st.selectbox("Timeframe", ["1m","5m","15m","1h","4h","1d"], index=3)
    venue = st.selectbox("Venue (OHLCV)", list(venues), index=0)
    horizon = st.number_input("Horizon candles", min_value=1, max_value=200, value=6, step=1)
    thr = st.number_input("Threshold (bps) for a 'hit'", min_value=0.0, max_value=500.0, value=5.0, step=1.0)
    symbol = st.text_input("Symbol filter (optional, canonical)", value="")
    inbox = SignalInboxSQLite()
    rows = inbox.list_signals(limit=5000, status=None, symbol=(symbol.strip() or None))
    if st.button("Compute + Store reliability now"):
        res = compute_and_store_reliability(
            inbox_rows=rows,
            venue=venue,
            timeframe=tf,
            horizon_candles=int(horizon),
            threshold_bps=float(thr),
            symbol=(symbol.strip() or None),
        )
        st.json(res)
    db = SignalReliabilitySQLite()
    rrows = db.list(limit=800, symbol=(symbol.strip() or None))
    df = pd.DataFrame(rrows)
    if len(df) > 0:
        st.subheader("Latest reliability rows")
        st.dataframe(df, width='stretch', height=300)
        st.subheader("Leaderboard (by hit_rate then avg_return_bps)")
        df2 = df.copy()
        df2 = df2.sort_values(["hit_rate","avg_return_bps","n_scored"], ascending=[False, False, False])
        st.dataframe(df2.head(30), width='stretch', height=280)
    else:
        st.info("No reliability rows yet. Click Compute + Store.")
except Exception as e:
    st.error(f"Signal Learning panel failed: {type(e).__name__}: {e}")
'''
    return t + "\n" + add

patch("dashboard/app.py", patch_dashboard)

# 6) Config validation: signals_learning.*
def patch_config_editor(t: str) -> str:
    if "signals_learning.min_hit_rate" in t and "signals_learning.scale_qty" in t:
        return t
    insert = """
    # Signals learning (optional)
    sl = cfg.get("signals_learning", {})
    if sl is not None and not isinstance(sl, dict):
        errors.append("signals_learning:must_be_mapping")
        sl = {}
    if isinstance(sl, dict):
        for k in ("enabled","scale_qty"):
            if k in sl and sl[k] is not None and not _is_bool(sl[k]):
                errors.append(f"signals_learning.{k}:must_be_bool")
        for k in ("min_n_scored","horizon_candles"):
            if k in sl and sl[k] is not None and not _is_int(sl[k]):
                errors.append(f"signals_learning.{k}:must_be_int")
        for k in ("min_hit_rate","qty_scale_min","qty_scale_max"):
            if k in sl and sl[k] is not None and not _is_float(sl[k]):
                errors.append(f"signals_learning.{k}:must_be_float")
        if "timeframe" in sl and sl["timeframe"] is not None:
            try: str(sl["timeframe"])
            except Exception: errors.append("signals_learning.timeframe:must_be_string")
        if "venue" in sl and sl["venue"] is not None:
            try: str(sl["venue"])
            except Exception: errors.append("signals_learning.venue:must_be_string")
"""
    anchor = "ok = len(errors) == 0"
    if anchor in t:
        return t.replace(anchor, insert + "\n" + anchor, 1)
    return t

patch("services/admin/config_editor.py", patch_config_editor)

# 7) install.py defaults: signals_learning block (OFF)
def patch_install_py(t: str) -> str:
    if "signals_learning:" in t:
        return t
    block = (
        "signals_learning:\n"
        " enabled: false\n"
        " venue: \"binance\"\n"
        " timeframe: \"1h\"\n"
        " horizon_candles: 6\n"
        " min_n_scored: 20\n"
        " min_hit_rate: 0.55\n"
        " scale_qty: false\n"
        " qty_scale_min: 0.5\n"
        " qty_scale_max: 1.5\n\n"
    )
    if "signals:\n" in t:
        return t.replace("signals:\n", block + "signals:\n", 1)
    return t + "\n# Added by Phase 125\n" + block

patch("install.py", patch_install_py)

# 8) CHECKPOINTS
def patch_checkpoints(t: str) -> str:
    if "## DU) Signal Learning v1 (Reliability Scoring)" in t:
        return t
    return t + (
        "\n## DU) Signal Learning v1 (Reliability Scoring)\n"
        "- ✅ DU1: signal_reliability.sqlite store (per source/author/symbol/venue/timeframe/horizon)\n"
        "- ✅ DU2: Reliability scoring (hit_rate + avg_return_bps) using OHLCV replay horizon\n"
        "- ✅ DU3: CLI recompute script (scripts/recompute_signal_reliability.py)\n"
        "- ✅ DU4: Dashboard panel compute/store + leaderboard\n"
        "- ✅ DU5: Optional learning gate + qty scaling for PAPER routing (signals_learning.*; default OFF)\n"
    )

patch("CHECKPOINTS.md", patch_checkpoints)

print("OK: Phase 125 applied (reliability scoring + store + dashboard + optional paper weighting + config + checkpoints).")
print("Next steps:")
print("  1. Run reliability recompute: python3 scripts/recompute_signal_reliability.py --venue binance --timeframe 1h --horizon 6 --threshold-bps 5.0")
print("  2. Check dashboard 'Signal Learning v1' panel for compute button + leaderboard")
print("  3. Enable signals_learning in config to use reliability gating/scaling in PAPER routing")
END_OF_FINAL