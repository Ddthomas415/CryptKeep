# apply_phase124.py - Phase 124: Signals inbox + webhook ingest + replay backtest + optional routing + config + checkpoints
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

# 1) Signal models + normalization
write("services/signals/models.py", r'''from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Literal, Dict, Any
from datetime import datetime, timezone
import uuid

Action = Literal["buy","sell","hold"]

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass
class SignalEvent:
    signal_id: str
    ts: str  # ISO string preferred
    source: str  # e.g. "tradingview_alert", "manual_import", "discord", "telegram"
    author: str  # public handle or label (not a private identity)
    venue_hint: str  # e.g. "binance" / "coinbase" / "gateio" or "" for unknown
    symbol: str  # canonical symbol e.g. BTC/USDT or BTC/USD
    action: Action
    confidence: float  # 0..1
    notes: str
    raw: Dict[str, Any]

def new_id() -> str:
    return str(uuid.uuid4())
''')

write("services/signals/normalizer.py", r'''from __future__ import annotations
from typing import Any, Dict, Optional
from services.signals.models import SignalEvent, new_id, utc_now_iso
from services.market_data.symbol_router import normalize_symbol, normalize_venue

def _f(x, default=0.0):
    try:
        v = float(x)
        if v != v:
            return default
        return v
    except Exception:
        return default

def normalize_signal(payload: Dict[str, Any]) -> SignalEvent:
    """
    Accepts a flexible JSON payload. Minimal required:
      - symbol
      - action (buy/sell/hold)
    Suggested:
      - source, author, venue_hint, confidence, ts, notes
    """
    symbol = normalize_symbol(str(payload.get("symbol") or payload.get("pair") or "").strip())
    action = str(payload.get("action") or payload.get("side") or "").lower().strip()
    if action not in ("buy","sell","hold"):
        # tolerate common variants
        if action in ("long","enter_long"):
            action = "buy"
        elif action in ("short","enter_short"):
            # spot-only scaffold: treat as sell (user can adapt later)
            action = "sell"
        else:
            action = "hold"
    source = str(payload.get("source") or "webhook").strip()
    author = str(payload.get("author") or payload.get("trader") or "unknown").strip()
    venue_hint = str(payload.get("venue") or payload.get("exchange") or payload.get("venue_hint") or "").strip()
    venue_hint = normalize_venue(venue_hint) if venue_hint else ""
    confidence = _f(payload.get("confidence"), 0.5)
    if confidence < 0: confidence = 0.0
    if confidence > 1: confidence = 1.0
    ts = str(payload.get("ts") or payload.get("timestamp") or payload.get("time") or utc_now_iso())
    notes = str(payload.get("notes") or payload.get("comment") or payload.get("message") or "").strip()
    return SignalEvent(
        signal_id=str(payload.get("signal_id") or new_id()),
        ts=ts,
        source=source,
        author=author,
        venue_hint=venue_hint,
        symbol=symbol,
        action=action,  # type: ignore
        confidence=confidence,
        notes=notes,
        raw=dict(payload),
    )
''')

# 2) Signal Inbox (SQLite)
write("storage/signal_inbox_sqlite.py", r'''from __future__ import annotations
import sqlite3
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from services.os.app_paths import data_dir

DB_PATH = data_dir() / "signal_inbox.sqlite"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS signal_inbox (
  signal_id TEXT PRIMARY KEY,
  ts TEXT NOT NULL,
  received_ts TEXT NOT NULL,
  source TEXT NOT NULL,
  author TEXT NOT NULL,
  venue_hint TEXT,
  symbol TEXT NOT NULL,
  action TEXT NOT NULL,
  confidence REAL NOT NULL,
  notes TEXT,
  raw_json TEXT NOT NULL,
  status TEXT NOT NULL,
  updated_ts TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_si_ts ON signal_inbox(ts);
CREATE INDEX IF NOT EXISTS idx_si_symbol_ts ON signal_inbox(symbol, ts);
CREATE INDEX IF NOT EXISTS idx_si_status ON signal_inbox(status);
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

class SignalInboxSQLite:
    def __init__(self) -> None:
        _connect().close()

    def upsert_signal(self, sig: Dict[str, Any]) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO signal_inbox(signal_id, ts, received_ts, source, author, venue_hint, symbol, action, confidence, notes, raw_json, status, updated_ts) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    str(sig["signal_id"]),
                    str(sig["ts"]),
                    str(sig.get("received_ts") or _now()),
                    str(sig.get("source") or "unknown"),
                    str(sig.get("author") or "unknown"),
                    sig.get("venue_hint"),
                    str(sig["symbol"]),
                    str(sig["action"]),
                    float(sig.get("confidence") or 0.5),
                    sig.get("notes"),
                    json.dumps(sig.get("raw") or {}, ensure_ascii=False),
                    str(sig.get("status") or "new"),
                    _now(),
                ),
            )
        finally:
            con.close()

    def list_signals(self, limit: int = 500, status: str | None = None, symbol: str | None = None) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            q = ("SELECT signal_id, ts, received_ts, source, author, venue_hint, symbol, action, confidence, notes, raw_json, status, updated_ts "
                 "FROM signal_inbox")
            args = []
            wh = []
            if status:
                wh.append("status=?"); args.append(str(status))
            if symbol:
                wh.append("symbol=?"); args.append(str(symbol))
            if wh:
                q += " WHERE " + " AND ".join(wh)
            q += " ORDER BY ts DESC LIMIT ?"
            args.append(int(limit))
            rows = con.execute(q, tuple(args)).fetchall()
            return [
                {
                    "signal_id": r[0], "ts": r[1], "received_ts": r[2], "source": r[3], "author": r[4],
                    "venue_hint": r[5], "symbol": r[6], "action": r[7], "confidence": r[8],
                    "notes": r[9], "raw": json.loads(r[10] or "{}"),
                    "status": r[11], "updated_ts": r[12],
                }
                for r in rows
            ]
        finally:
            con.close()

    def set_status(self, signal_id: str, status: str) -> None:
        con = _connect()
        try:
            con.execute("UPDATE signal_inbox SET status=?, updated_ts=? WHERE signal_id=?", (str(status), _now(), str(signal_id)))
        finally:
            con.close()
''')

# 3) Webhook server (stdlib http.server) to receive signals
write("services/signals/webhook_server.py", r'''from __future__ import annotations
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from datetime import datetime, timezone
from services.signals.normalizer import normalize_signal
from storage.signal_inbox_sqlite import SignalInboxSQLite

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

class Handler(BaseHTTPRequestHandler):
    inbox = SignalInboxSQLite()

    def _send(self, code: int, obj: dict):
        raw = (json.dumps(obj, indent=2, sort_keys=True) + "\n").encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        u = urlparse(self.path)
        if u.path not in ("/signal", "/signals"):
            self._send(404, {"ok": False, "reason": "not_found", "path": u.path})
            return
        try:
            n = int(self.headers.get("Content-Length", "0") or "0")
            body = self.rfile.read(n) if n > 0 else b"{}"
            payload = json.loads(body.decode("utf-8", errors="replace"))
            if not isinstance(payload, dict):
                raise ValueError("payload_must_be_object")
            sig = normalize_signal(payload)
            self.inbox.upsert_signal({
                "signal_id": sig.signal_id,
                "ts": sig.ts,
                "received_ts": _now(),
                "source": sig.source,
                "author": sig.author,
                "venue_hint": sig.venue_hint,
                "symbol": sig.symbol,
                "action": sig.action,
                "confidence": sig.confidence,
                "notes": sig.notes,
                "raw": sig.raw,
                "status": "new",
            })
            self._send(200, {"ok": True, "signal_id": sig.signal_id})
        except Exception as e:
            self._send(400, {"ok": False, "reason": f"{type(e).__name__}:{e}"})

    def log_message(self, fmt, *args):
        return

def run(host: str = "127.0.0.1", port: int = 8787):
    srv = HTTPServer((host, int(port)), Handler)
    print({"ok": True, "listening": f"http://{host}:{port}", "post_to": "/signal"})
    srv.serve_forever()
''')

write("scripts/run_signal_webhook.py", r'''#!/usr/bin/env python3
from __future__ import annotations
import argparse
from services.signals.webhook_server import run

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8787)
    args = ap.parse_args()
    run(args.host, args.port)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
''')

# 4) Optional: route reviewed signals into PAPER intents (OFF by default, allowlist)
write("services/signals/routing.py", r'''from __future__ import annotations
import time
import uuid
from services.admin.config_editor import load_user_yaml
from services.market_data.symbol_router import normalize_venue, normalize_symbol
from storage.intent_queue_sqlite import IntentQueueSQLite

def _cfg() -> dict:
    cfg = load_user_yaml()
    r = cfg.get("signals") if isinstance(cfg.get("signals"), dict) else {}
    return {
        "auto_route_to_paper": bool(r.get("auto_route_to_paper", False)),
        "allowed_sources": r.get("allowed_sources") if isinstance(r.get("allowed_sources"), list) else [],
        "allowed_authors": r.get("allowed_authors") if isinstance(r.get("allowed_authors"), list) else [],
        "allowed_symbols": r.get("allowed_symbols") if isinstance(r.get("allowed_symbols"), list) else [],
        "default_venue": normalize_venue(str(r.get("default_venue", "binance") or "binance")),
        "default_qty": float(r.get("default_qty", 0.001) or 0.001),
        "order_type": str(r.get("order_type", "market") or "market").lower().strip(),
    }

def _allowed(val: str, allowed_list: list[str]) -> bool:
    if not allowed_list:
        return True
    return val in set(str(x) for x in allowed_list)

def route_signal_to_paper_intent(sig: dict) -> dict:
    """
    Creates a paper intent from a signal, only if config allows and allowlists pass.
    """
    cfg = _cfg()
    if not cfg["auto_route_to_paper"]:
        return {"ok": False, "reason": "signals.auto_route_to_paper_disabled"}
    source = str(sig.get("source") or "")
    author = str(sig.get("author") or "")
    symbol = normalize_symbol(str(sig.get("symbol") or ""))
    action = str(sig.get("action") or "").lower().strip()
    if action not in ("buy","sell"):
        return {"ok": False, "reason": "signal_action_not_tradeable", "action": action}
    if not _allowed(source, cfg["allowed_sources"]):
        return {"ok": False, "reason": "source_not_allowed", "source": source}
    if not _allowed(author, cfg["allowed_authors"]):
        return {"ok": False, "reason": "author_not_allowed", "author": author}
    if cfg["allowed_symbols"] and symbol not in set(normalize_symbol(str(s)) for s in cfg["allowed_symbols"]):
        return {"ok": False, "reason": "symbol_not_allowed", "symbol": symbol}
    venue = normalize_venue(str(sig.get("venue_hint") or cfg["default_venue"]))
    qty = float(sig.get("qty") or cfg["default_qty"])
    intent_id = str(uuid.uuid4())
    it = {
        "intent_id": intent_id,
        "ts": str(int(time.time())),
        "source": "signal_inbox",
        "venue": venue,
        "symbol": symbol,
        "side": action,
        "order_type": cfg["order_type"],
        "qty": qty,
        "limit_price": None,
        "status": "queued",
        "last_error": None,
    }
    db = IntentQueueSQLite()
    db.upsert_intent(it)
    return {"ok": True, "intent_id": intent_id, "intent": it}
''')

# 5) Signal replay backtest (simple, CCXT OHLCV)
write("services/backtest/signal_replay.py", r'''from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import math
import time
from services.security.exchange_factory import make_exchange
from services.market_data.symbol_router import normalize_venue, map_symbol, normalize_symbol

def _f(x, default=0.0):
    try:
        v = float(x)
        if not math.isfinite(v):
            return default
        return v
    except Exception:
        return default

def fetch_ohlcv(venue: str, canonical_symbol: str, timeframe: str = "1h", limit: int = 500) -> list[list]:
    v = normalize_venue(venue)
    sym = map_symbol(v, normalize_symbol(canonical_symbol))
    ex = make_exchange(v, {"apiKey": None, "secret": None}, enable_rate_limit=True)
    try:
        return ex.fetch_ohlcv(sym, timeframe=timeframe, limit=int(limit))
    finally:
        try:
            if hasattr(ex, "close"):
                ex.close()
        except Exception:
            pass

def replay_signals_on_ohlcv(
    ohlcv: list[list],
    signals: list[dict],
    *,
    fee_bps: float = 10.0,  # 0.10%
    slippage_bps: float = 5.0,  # 0.05%
    initial_cash: float = 10000.0,
) -> dict:
    sigs = []
    for s in signals:
        ts_ms = s.get("ts_ms")
        if ts_ms is None:
            try:
                ts_ms = int(float(s.get("ts")) * 1000.0)
            except Exception:
                ts_ms = 0
        sigs.append({**s, "ts_ms": int(ts_ms)})
    sigs.sort(key=lambda r: int(r.get("ts_ms") or 0))
    cash = float(initial_cash)
    pos_qty = 0.0
    pos_entry_px = None
    equity = []
    trades = []
    def find_next_idx(ts_ms: int) -> int:
        for i, row in enumerate(ohlcv):
            if int(row[0]) >= ts_ms:
                return i
        return len(ohlcv) - 1
    sig_i = 0
    for i, row in enumerate(ohlcv):
        t_ms = int(row[0])
        o = _f(row[1]); c = _f(row[4])
        while sig_i < len(sigs) and find_next_idx(sigs[sig_i]["ts_ms"]) == i:
            s = sigs[sig_i]
            act = str(s.get("action") or "").lower().strip()
            px = o
            slip = px * (slippage_bps / 10000.0)
            fee = 0.0
            if act == "buy" and pos_qty <= 1e-12:
                exec_px = px + slip
                qty = cash / exec_px if exec_px > 0 else 0.0
                notional = qty * exec_px
                fee = notional * (fee_bps / 10000.0)
                if qty > 0 and cash >= fee:
                    cash = cash - notional - fee
                    pos_qty = qty
                    pos_entry_px = exec_px
                    trades.append({"ts_ms": t_ms, "action": "buy", "qty": qty, "px": exec_px, "fee": fee})
            elif act == "sell" and pos_qty > 1e-12:
                exec_px = max(px - slip, 0.0)
                notional = pos_qty * exec_px
                fee = notional * (fee_bps / 10000.0)
                cash = cash + notional - fee
                trades.append({"ts_ms": t_ms, "action": "sell", "qty": pos_qty, "px": exec_px, "fee": fee})
                pos_qty = 0.0
                pos_entry_px = None
            sig_i += 1
        mtm = cash + pos_qty * c
        equity.append({"ts_ms": t_ms, "equity": mtm, "cash": cash, "pos_qty": pos_qty, "close": c})
    realized = 0.0
    last_buy = None
    for tr in trades:
        if tr["action"] == "buy":
            last_buy = tr
        elif tr["action"] == "sell" and last_buy:
            realized += (tr["px"] - last_buy["px"]) * last_buy["qty"] - (tr["fee"] + last_buy["fee"])
            last_buy = None
    return {
        "initial_cash": initial_cash,
        "final_equity": equity[-1]["equity"] if equity else initial_cash,
        "realized_pnl_est": realized,
        "trades": trades,
        "equity": equity,
        "signals_used": len(sigs),
    }
''')

# 6) Dashboard panel: Signal Inbox + webhook starter + replay backtest + optional routing
def patch_dashboard(t: str) -> str:
    if "Signal Inbox + Trader Learning (Public Signals Only)" in t:
        return t
    add = r'''
st.divider()
st.header("Signal Inbox + Trader Learning (Public Signals Only)")
st.caption("Ingests voluntary/public signals via webhook or manual import. No private account access. Replay/backtest available. Optional routing to PAPER intents is OFF by default.")
try:
    import pandas as pd
    import json as _json
    import subprocess as _subprocess
    import sys as _sys
    import platform as _platform
    import uuid as _uuid
    import time as _time
    from storage.signal_inbox_sqlite import SignalInboxSQLite
    from services.signals.normalizer import normalize_signal
    from services.signals.routing import route_signal_to_paper_intent
    from services.backtest.signal_replay import fetch_ohlcv, replay_signals_on_ohlcv
    from services.admin.config_editor import load_user_yaml
    db = SignalInboxSQLite()
    st.subheader("Webhook receiver (local)")
    st.code("POST http://127.0.0.1:8787/signal (JSON body)", language="text")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Start webhook server (background)"):
            cmd = [_sys.executable, "scripts/run_signal_webhook.py", "--host", "127.0.0.1", "--port", "8787"]
            try:
                if _platform.system().lower().startswith("win"):
                    DETACHED_PROCESS = 0x00000008
                    _subprocess.Popen(cmd, creationflags=DETACHED_PROCESS, stdout=_subprocess.DEVNULL, stderr=_subprocess.DEVNULL)
                else:
                    _subprocess.Popen(cmd, start_new_session=True, stdout=_subprocess.DEVNULL, stderr=_subprocess.DEVNULL)
                st.success({"ok": True, "started": cmd})
            except Exception as e:
                st.error(f"Start failed: {type(e).__name__}: {e}")
    with c2:
        st.caption("Example payload")
        st.code(_json.dumps({
            "source": "tradingview_alert",
            "author": "public_handle",
            "venue_hint": "binance",
            "symbol": "BTC/USDT",
            "action": "buy",
            "confidence": 0.7,
            "notes": "breakout",
            "ts": int(_time.time())
        }, indent=2), language="json")
    st.subheader("Manual import (single JSON)")
    raw = st.text_area("Paste JSON object here", value="", height=120)
    if st.button("Import JSON to inbox"):
        try:
            payload = _json.loads(raw)
            sig = normalize_signal(payload)
            db.upsert_signal({
                "signal_id": sig.signal_id,
                "ts": sig.ts,
                "received_ts": None,
                "source": sig.source,
                "author": sig.author,
                "venue_hint": sig.venue_hint,
                "symbol": sig.symbol,
                "action": sig.action,
                "confidence": sig.confidence,
                "notes": sig.notes,
                "raw": sig.raw,
                "status": "new",
            })
            st.success({"ok": True, "signal_id": sig.signal_id})
        except Exception as e:
            st.error(f"Import failed: {type(e).__name__}: {e}")
    st.subheader("Inbox")
    filt_status = st.selectbox("Filter status", ["(all)", "new", "reviewed", "ignored", "routed"], index=0)
    rows = db.list_signals(limit=400, status=None if filt_status=="(all)" else filt_status)
    df = pd.DataFrame([{
        "signal_id": r["signal_id"],
        "ts": r["ts"],
        "source": r["source"],
        "author": r["author"],
        "venue_hint": r.get("venue_hint"),
        "symbol": r["symbol"],
        "action": r["action"],
        "confidence": r["confidence"],
        "status": r["status"],
        "notes": r.get("notes",""),
    } for r in rows])
    st.dataframe(df, width='stretch', height=260)
    st.subheader("Review / Route")
    pick = st.text_input("Signal ID to act on", value="")
    c3, c4, c5 = st.columns(3)
    with c3:
        if st.button("Mark REVIEWED"):
            db.set_status(pick, "reviewed")
            st.success("updated")
    with c4:
        if st.button("Mark IGNORED"):
            db.set_status(pick, "ignored")
            st.success("updated")
    with c5:
        if st.button("Route to PAPER intent (if enabled)"):
            full = next((r for r in rows if r["signal_id"] == pick), None)
            if not full:
                st.error("Signal not found in current list (adjust filter or refresh).")
            else:
                out = route_signal_to_paper_intent(full)
                st.json(out)
                if out.get("ok"):
                    db.set_status(pick, "routed")
    st.subheader("Replay Backtest (signals → OHLCV)")
    cfg = load_user_yaml()
    venues = (cfg.get("preflight", {}).get("venues") if isinstance(cfg.get("preflight"), dict) else None) or ["binance","coinbase","gateio"]
    default_venue = venues[0] if venues else "binance"
    bt_venue = st.selectbox("OHLCV venue (public)", list(venues), index=0)
    bt_symbol = st.text_input("Canonical symbol", value="BTC/USDT")
    timeframe = st.selectbox("Timeframe", ["1m","5m","15m","1h","4h","1d"], index=3)
    limit = st.number_input("Candles limit", min_value=100, max_value=2000, value=600, step=50)
    sym_rows = [r for r in rows if str(r.get("symbol")) == bt_symbol]
    st.caption(f"Signals in inbox matching symbol: {len(sym_rows)}")
    if st.button("Run replay backtest"):
        try:
            ohlcv = fetch_ohlcv(bt_venue, bt_symbol, timeframe=timeframe, limit=int(limit))
            sigs = []
            for r in sym_rows:
                ts_ms = None
                try:
                    ts_ms = int(float(r.get("ts")) * 1000.0)
                except Exception:
                    ts_ms = 0
                sigs.append({"ts_ms": ts_ms, "action": r.get("action"), "confidence": r.get("confidence")})
            res = replay_signals_on_ohlcv(ohlcv, sigs)
            st.json({k: res[k] for k in ("initial_cash","final_equity","realized_pnl_est","signals_used")})
            eq = pd.DataFrame(res["equity"])
            if len(eq) > 0:
                eq2 = eq.copy()
                eq2["ts_ms"] = eq2["ts_ms"].astype("int64")
                st.line_chart(eq2.set_index("ts_ms")["equity"])
            st.dataframe(pd.DataFrame(res["trades"]), width='stretch', height=220)
        except Exception as e:
            st.error(f"Replay failed: {type(e).__name__}: {e}")
    st.subheader("Signal routing config (OFF by default)")
    st.json(cfg.get("signals", {}))
except Exception as e:
    st.error(f"Signal Inbox panel failed: {type(e).__name__}: {e}")
'''
    return t + "\n" + add

patch("dashboard/app.py", patch_dashboard)

# 7) Config validation additions for signals
def patch_config_editor(t: str) -> str:
    if "signals.auto_route_to_paper" in t and "signals.allowed_sources" in t:
        return t
    insert = """
    # Signals routing (optional)
    sg = cfg.get("signals", {})
    if sg is not None and not isinstance(sg, dict):
        errors.append("signals:must_be_mapping")
        sg = {}
    if isinstance(sg, dict):
        if "auto_route_to_paper" in sg and sg["auto_route_to_paper"] is not None and not _is_bool(sg["auto_route_to_paper"]):
            errors.append("signals.auto_route_to_paper:must_be_bool")
        for k in ("allowed_sources","allowed_authors","allowed_symbols"):
            if k in sg and sg[k] is not None and not isinstance(sg[k], list):
                errors.append(f"signals.{k}:must_be_list")
        if "default_venue" in sg and sg["default_venue"] is not None:
            try: str(sg["default_venue"])
            except Exception: errors.append("signals.default_venue:must_be_string")
        if "default_qty" in sg and sg["default_qty"] is not None and not _is_float(sg["default_qty"]):
            errors.append("signals.default_qty:must_be_float")
        if "order_type" in sg and sg["order_type"] is not None:
            try: str(sg["order_type"])
            except Exception: errors.append("signals.order_type:must_be_string")
"""
    anchor = "ok = len(errors) == 0"
    if anchor in t:
        return t.replace(anchor, insert + "\n" + anchor, 1)
    return t

patch("services/admin/config_editor.py", patch_config_editor)

# 8) install.py defaults: signals block (routing OFF)
def patch_install_py(t: str) -> str:
    if "signals:" in t:
        return t
    block = (
        "signals:\n"
        " auto_route_to_paper: false\n"
        " allowed_sources: [\"tradingview_alert\", \"manual_import\", \"webhook\"]\n"
        " allowed_authors: []\n"
        " allowed_symbols: [\"BTC/USDT\"]\n"
        " default_venue: \"binance\"\n"
        " default_qty: 0.001\n"
        " order_type: \"market\"\n\n"
    )
    if "preflight:\n" in t:
        return t.replace("preflight:\n", block + "preflight:\n", 1)
    return t + "\n# Added by Phase 124\n" + block

patch("install.py", patch_install_py)

# 9) CHECKPOINTS
def patch_checkpoints(t: str) -> str:
    if "## DT) Trader Learning Ingestion Scaffold (Public Signals)" in t:
        return t
    return t + (
        "\n## DT) Trader Learning Ingestion Scaffold (Public Signals)\n"
        "- ✅ DT1: SignalEvent model + normalizer (accepts flexible payloads → canonical)\n"
        "- ✅ DT2: signal_inbox.sqlite store with statuses (new/reviewed/ignored/routed)\n"
        "- ✅ DT3: Local webhook receiver (POST /signal) to ingest signals safely\n"
        "- ✅ DT4: Dashboard Signal Inbox page (view, review, ignore, optional route-to-paper)\n"
        "- ✅ DT5: Signal replay backtest scaffold (signals → CCXT OHLCV → equity/trades)\n"
        "- ✅ DT6: Routing allowlists + default routing OFF (requires explicit enable)\n"
    )

patch("CHECKPOINTS.md", patch_checkpoints)

print("OK: Phase 124 applied (signals inbox + webhook ingest + replay backtest + optional routing + config + checkpoints).")
print("Next steps:")
print("  1. Start webhook server: python3 scripts/run_signal_webhook.py")
print("  2. Check dashboard 'Signal Inbox' panel for webhook URL + manual import + inbox table")
print("  3. Enqueue test signal via webhook (POST http://127.0.0.1:8787/signal) or manual JSON import")
print("  4. Review/route signals or run replay backtest in dashboard")
END_OF_FINAL