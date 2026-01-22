# apply_phase109.py - Phase 109 launcher (paper execution engine + db + runner + dashboard)
from pathlib import Path
import re

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

# 1) Paper trading DB
write("storage/paper_trading_sqlite.py", r'''from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
from services.os.app_paths import data_dir

DB_PATH = data_dir() / "paper_trading.sqlite"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS paper_state (
  k TEXT PRIMARY KEY,
  v TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS paper_orders (
  order_id TEXT PRIMARY KEY,
  client_order_id TEXT NOT NULL UNIQUE, -- idempotency key
  created_ts TEXT NOT NULL,
  ts TEXT NOT NULL, -- intended timestamp
  venue TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  order_type TEXT NOT NULL,
  qty REAL NOT NULL,
  limit_price REAL,
  status TEXT NOT NULL,
  reject_reason TEXT
);
CREATE INDEX IF NOT EXISTS idx_po_ts ON paper_orders(ts);
CREATE INDEX IF NOT EXISTS idx_po_symbol ON paper_orders(symbol);
CREATE INDEX IF NOT EXISTS idx_po_status ON paper_orders(status);
CREATE TABLE IF NOT EXISTS paper_fills (
  fill_id TEXT PRIMARY KEY,
  order_id TEXT NOT NULL,
  ts TEXT NOT NULL,
  price REAL NOT NULL,
  qty REAL NOT NULL,
  fee REAL NOT NULL,
  fee_currency TEXT NOT NULL,
  FOREIGN KEY(order_id) REFERENCES paper_orders(order_id)
);
CREATE INDEX IF NOT EXISTS idx_pf_order ON paper_fills(order_id);
CREATE INDEX IF NOT EXISTS idx_pf_ts ON paper_fills(ts);
CREATE TABLE IF NOT EXISTS paper_positions (
  symbol TEXT PRIMARY KEY,
  qty REAL NOT NULL,
  avg_price REAL NOT NULL,
  realized_pnl REAL NOT NULL,
  updated_ts TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS paper_equity (
  ts TEXT PRIMARY KEY,
  cash_quote REAL NOT NULL,
  equity_quote REAL NOT NULL,
  unrealized_pnl REAL NOT NULL,
  realized_pnl REAL NOT NULL
);
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

class PaperTradingSQLite:
    def __init__(self) -> None:
        _connect().close()

    def get_state(self, k: str) -> Optional[str]:
        con = _connect()
        try:
            r = con.execute("SELECT v FROM paper_state WHERE k=?", (str(k),)).fetchone()
            return r[0] if r else None
        finally:
            con.close()

    def set_state(self, k: str, v: str) -> None:
        con = _connect()
        try:
            con.execute("INSERT OR REPLACE INTO paper_state(k,v) VALUES(?,?)", (str(k), str(v)))
        finally:
            con.close()

    def insert_order(self, row: Dict[str, Any]) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO paper_orders(order_id, client_order_id, created_ts, ts, venue, symbol, side, order_type, qty, limit_price, status, reject_reason) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    str(row["order_id"]),
                    str(row["client_order_id"]),
                    _now(),
                    str(row["ts"]),
                    str(row["venue"]),
                    str(row["symbol"]),
                    str(row["side"]),
                    str(row["order_type"]),
                    float(row["qty"]),
                    row.get("limit_price"),
                    str(row["status"]),
                    row.get("reject_reason"),
                ),
            )
        finally:
            con.close()

    def get_order_by_client_id(self, client_order_id: str) -> Optional[Dict[str, Any]]:
        con = _connect()
        try:
            r = con.execute(
                "SELECT order_id, client_order_id, created_ts, ts, venue, symbol, side, order_type, qty, limit_price, status, reject_reason "
                "FROM paper_orders WHERE client_order_id=?",
                (str(client_order_id),),
            ).fetchone()
            if not r:
                return None
            return {
                "order_id": r[0], "client_order_id": r[1], "created_ts": r[2], "ts": r[3],
                "venue": r[4], "symbol": r[5], "side": r[6], "order_type": r[7],
                "qty": r[8], "limit_price": r[9], "status": r[10], "reject_reason": r[11],
            }
        finally:
            con.close()

    def update_order_status(self, order_id: str, status: str, reject_reason: str | None = None) -> None:
        con = _connect()
        try:
            con.execute("UPDATE paper_orders SET status=?, reject_reason=? WHERE order_id=?", (str(status), reject_reason, str(order_id)))
        finally:
            con.close()

    def list_orders(self, limit: int = 500, status: str | None = None) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            q = ("SELECT order_id, client_order_id, created_ts, ts, venue, symbol, side, order_type, qty, limit_price, status, reject_reason "
                 "FROM paper_orders")
            args = []
            if status:
                q += " WHERE status=?"
                args.append(str(status))
            q += " ORDER BY created_ts DESC LIMIT ?"
            args.append(int(limit))
            rows = con.execute(q, tuple(args)).fetchall()
            return [
                {
                    "order_id": r[0], "client_order_id": r[1], "created_ts": r[2], "ts": r[3],
                    "venue": r[4], "symbol": r[5], "side": r[6], "order_type": r[7],
                    "qty": r[8], "limit_price": r[9], "status": r[10], "reject_reason": r[11],
                }
                for r in rows
            ]
        finally:
            con.close()

    def insert_fill(self, row: Dict[str, Any]) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO paper_fills(fill_id, order_id, ts, price, qty, fee, fee_currency) VALUES(?,?,?,?,?,?,?)",
                (str(row["fill_id"]), str(row["order_id"]), str(row["ts"]), float(row["price"]), float(row["qty"]), float(row["fee"]), str(row["fee_currency"])),
            )
        finally:
            con.close()

    def list_fills(self, limit: int = 500) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            rows = con.execute(
                "SELECT fill_id, order_id, ts, price, qty, fee, fee_currency FROM paper_fills ORDER BY ts DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
            return [{"fill_id": r[0], "order_id": r[1], "ts": r[2], "price": r[3], "qty": r[4], "fee": r[5], "fee_currency": r[6]} for r in rows]
        finally:
            con.close()

    def upsert_position(self, symbol: str, qty: float, avg_price: float, realized_pnl: float) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO paper_positions(symbol, qty, avg_price, realized_pnl, updated_ts) VALUES(?,?,?,?,?)",
                (str(symbol), float(qty), float(avg_price), float(realized_pnl), _now()),
            )
        finally:
            con.close()

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        con = _connect()
        try:
            r = con.execute("SELECT symbol, qty, avg_price, realized_pnl, updated_ts FROM paper_positions WHERE symbol=?", (str(symbol),)).fetchone()
            if not r:
                return None
            return {"symbol": r[0], "qty": r[1], "avg_price": r[2], "realized_pnl": r[3], "updated_ts": r[4]}
        finally:
            con.close()

    def list_positions(self, limit: int = 200) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            rows = con.execute(
                "SELECT symbol, qty, avg_price, realized_pnl, updated_ts FROM paper_positions ORDER BY updated_ts DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
            return [{"symbol": r[0], "qty": r[1], "avg_price": r[2], "realized_pnl": r[3], "updated_ts": r[4]} for r in rows]
        finally:
            con.close()

    def insert_equity(self, ts: str, cash_quote: float, equity_quote: float, unrealized_pnl: float, realized_pnl: float) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO paper_equity(ts, cash_quote, equity_quote, unrealized_pnl, realized_pnl) VALUES(?,?,?,?,?)",
                (str(ts), float(cash_quote), float(equity_quote), float(unrealized_pnl), float(realized_pnl)),
            )
        finally:
            con.close()

    def list_equity(self, limit: int = 2000) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            rows = con.execute(
                "SELECT ts, cash_quote, equity_quote, unrealized_pnl, realized_pnl FROM paper_equity ORDER BY ts DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
            return [{"ts": r[0], "cash_quote": r[1], "equity_quote": r[2], "unrealized_pnl": r[3], "realized_pnl": r[4]} for r in rows]
        finally:
            con.close()
''')

# 2) Tick reader for pricing (prefer system_status.latest.json)
write("services/market_data/tick_reader.py", r'''from __future__ import annotations
import json
from pathlib import Path
from typing import Optional, Tuple
from services.os.app_paths import runtime_dir

LATEST = runtime_dir() / "snapshots" / "system_status.latest.json"

def get_best_bid_ask_last(venue: str, symbol: str) -> Optional[dict]:
    try:
        if not LATEST.exists():
            return None
        snap = json.loads(LATEST.read_text(encoding="utf-8"))
        ticks = snap.get("ticks") if isinstance(snap, dict) else None
        if not isinstance(ticks, list):
            return None
        v = str(venue).lower().strip()
        s = str(symbol).strip()
        # pick the most recent matching tick
        best = None
        for t in ticks:
            if not isinstance(t, dict):
                continue
            if str(t.get("venue","")).lower().strip() == v and str(t.get("symbol","")).strip() == s:
                best = t
        if not best:
            return None
        return {
            "ts_ms": int(best.get("ts_ms") or 0),
            "bid": best.get("bid"),
            "ask": best.get("ask"),
            "last": best.get("last"),
        }
    except Exception:
        return None

def mid_price(q: dict) -> Optional[float]:
    try:
        b = q.get("bid")
        a = q.get("ask")
        if b is None or a is None:
            l = q.get("last")
            return float(l) if l is not None else None
        return (float(b) + float(a)) / 2.0
    except Exception:
        return None
''')

# 3) Paper execution engine
write("services/execution/paper_engine.py", r'''from __future__ import annotations
import json
import math
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from services.admin.config_editor import load_user_yaml
from services.market_data.tick_reader import get_best_bid_ask_last, mid_price
from services.security.exchange_factory import make_exchange
from storage.paper_trading_sqlite import PaperTradingSQLite

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _cfg() -> dict:
    cfg = load_user_yaml()
    p = cfg.get("paper_trading") if isinstance(cfg.get("paper_trading"), dict) else {}
    return {
        "enabled": bool(p.get("enabled", True)),
        "quote_currency": str(p.get("quote_currency", "USDT") or "USDT"),
        "starting_cash_quote": float(p.get("starting_cash_quote", 10000.0) or 10000.0),
        "fee_bps": float(p.get("fee_bps", 7.5) or 7.5),
        "slippage_bps": float(p.get("slippage_bps", 5.0) or 5.0),
        "use_ccxt_fallback": bool(p.get("use_ccxt_fallback", True)),
        "max_order_qty": float(p.get("max_order_qty", 1e9) or 1e9),
    }

class PaperEngine:
    def __init__(self) -> None:
        self.db = PaperTradingSQLite()
        self.cfg = _cfg()
        self._ensure_cash_initialized()

    def _ensure_cash_initialized(self) -> None:
        v = self.db.get_state("cash_quote")
        if v is None:
            self.db.set_state("cash_quote", str(self.cfg["starting_cash_quote"]))
        if self.db.get_state("realized_pnl") is None:
            self.db.set_state("realized_pnl", "0.0")

    def cash_quote(self) -> float:
        v = self.db.get_state("cash_quote") or "0"
        try:
            return float(v)
        except Exception:
            return 0.0

    def set_cash_quote(self, x: float) -> None:
        self.db.set_state("cash_quote", str(float(x)))

    def realized_pnl(self) -> float:
        v = self.db.get_state("realized_pnl") or "0"
        try:
            return float(v)
        except Exception:
            return 0.0

    def set_realized_pnl(self, x: float) -> None:
        self.db.set_state("realized_pnl", str(float(x)))

    def _price(self, venue: str, symbol: str) -> Optional[dict]:
        q = get_best_bid_ask_last(venue, symbol)
        if q:
            return q
        if not self.cfg["use_ccxt_fallback"]:
            return None
        ex = make_exchange(str(venue).lower().strip(), {"apiKey": None, "secret": None}, enable_rate_limit=True)
        try:
            t = ex.fetch_ticker(symbol)
            return {
                "ts_ms": int(t.get("timestamp") or 0),
                "bid": t.get("bid"),
                "ask": t.get("ask"),
                "last": t.get("last"),
            }
        finally:
            try:
                if hasattr(ex, "close"):
                    ex.close()
            except Exception:
                pass

    def submit_order(
        self,
        *,
        client_order_id: str,
        venue: str,
        symbol: str,
        side: str,
        order_type: str,
        qty: float,
        limit_price: float | None = None,
        ts: str | None = None,
    ) -> dict:
        existing = self.db.get_order_by_client_id(client_order_id)
        if existing:
            return {"ok": True, "idempotent": True, "order": existing}
        side = str(side).lower().strip()
        order_type = str(order_type).lower().strip()
        if side not in ("buy", "sell"):
            return {"ok": False, "reason": "bad_side"}
        if order_type not in ("market", "limit"):
            return {"ok": False, "reason": "bad_order_type"}
        qty = float(qty)
        if not (qty > 0.0) or not math.isfinite(qty):
            return {"ok": False, "reason": "bad_qty"}
        if qty > float(self.cfg["max_order_qty"]):
            return {"ok": False, "reason": "qty_exceeds_max"}
        if order_type == "limit":
            if limit_price is None:
                return {"ok": False, "reason": "missing_limit_price"}
            limit_price = float(limit_price)
            if not (limit_price > 0.0) or not math.isfinite(limit_price):
                return {"ok": False, "reason": "bad_limit_price"}
        oid = str(uuid.uuid4())
        row = {
            "order_id": oid,
            "client_order_id": str(client_order_id),
            "ts": str(ts or _now()),
            "venue": str(venue).lower().strip(),
            "symbol": str(symbol).strip(),
            "side": side,
            "order_type": order_type,
            "qty": qty,
            "limit_price": limit_price,
            "status": "new",
            "reject_reason": None,
        }
        self.db.insert_order(row)
        self.evaluate_open_orders()
        out = self.db.get_order_by_client_id(client_order_id)
        return {"ok": True, "idempotent": False, "order": out}

    def cancel_order(self, client_order_id: str) -> dict:
        o = self.db.get_order_by_client_id(client_order_id)
        if not o:
            return {"ok": False, "reason": "not_found"}
        if o["status"] in ("filled", "canceled", "rejected"):
            return {"ok": True, "already_final": True, "order": o}
        self.db.update_order_status(o["order_id"], "canceled", None)
        return {"ok": True, "order": self.db.get_order_by_client_id(client_order_id)}

    def _apply_fill(self, order: dict, price: float, qty: float) -> dict:
        fee_bps = float(self.cfg["fee_bps"])
        fee = (price * qty) * (fee_bps / 10000.0)
        fee_ccy = self.cfg["quote_currency"]
        fill_id = str(uuid.uuid4())
        self.db.insert_fill({"fill_id": fill_id, "order_id": order["order_id"], "ts": _now(), "price": float(price), "qty": float(qty), "fee": float(fee), "fee_currency": str(fee_ccy)})
        pos = self.db.get_position(order["symbol"]) or {"symbol": order["symbol"], "qty": 0.0, "avg_price": 0.0, "realized_pnl": 0.0}
        pos_qty = float(pos["qty"])
        avg = float(pos["avg_price"])
        realized = float(pos["realized_pnl"])
        cash = self.cash_quote()
        if order["side"] == "buy":
            cost = price * qty + fee
            if cash < cost:
                self.db.update_order_status(order["order_id"], "rejected", "insufficient_cash")
                return {"ok": False, "reason": "insufficient_cash"}
            new_qty = pos_qty + qty
            new_avg = ((avg * pos_qty) + (price * qty)) / new_qty if new_qty > 0 else 0.0
            self.db.upsert_position(order["symbol"], new_qty, new_avg, realized)
            self.set_cash_quote(cash - cost)
        else:
            if pos_qty < qty:
                self.db.update_order_status(order["order_id"], "rejected", "insufficient_position")
                return {"ok": False, "reason": "insufficient_position"}
            proceeds = price * qty - fee
            pnl = (price - avg) * qty
            realized2 = realized + pnl
            new_qty = pos_qty - qty
            new_avg = avg if new_qty > 0 else 0.0
            self.db.upsert_position(order["symbol"], new_qty, new_avg, realized2)
            self.set_cash_quote(cash + proceeds)
            self.set_realized_pnl(self.realized_pnl() + pnl)
            self.db.update_order_status(order["order_id"], "filled", None)
        return {"ok": True, "fill_id": fill_id, "fee": fee}

    def evaluate_open_orders(self) -> dict:
        orders = self.db.list_orders(limit=2000, status="new")
        n_filled = 0
        n_rejected = 0
        details = []
        for o in orders:
            q = self._price(o["venue"], o["symbol"])
            if not q:
                continue
            m = mid_price(q)
            if m is None:
                continue
            slip_bps = float(self.cfg["slippage_bps"])
            if o["order_type"] == "market":
                if o["side"] == "buy":
                    px = m * (1.0 + slip_bps / 10000.0)
                else:
                    px = m * (1.0 - slip_bps / 10000.0)
                res = self._apply_fill(o, px, float(o["qty"]))
                if res.get("ok"):
                    n_filled += 1
                else:
                    n_rejected += 1
                details.append({"client_order_id": o["client_order_id"], "result": res})
                continue
            bid = q.get("bid")
            ask = q.get("ask")
            px_bid = float(bid) if bid is not None else float(m)
            px_ask = float(ask) if ask is not None else float(m)
            lim = float(o["limit_price"] or 0.0)
            should_fill = False
            fill_px = None
            if o["side"] == "buy":
                if lim >= px_ask:
                    should_fill = True
                    fill_px = min(lim, px_ask)
            else:
                if lim <= px_bid:
                    should_fill = True
                    fill_px = max(lim, px_bid)
            if should_fill and fill_px is not None:
                res = self._apply_fill(o, float(fill_px), float(o["qty"]))
                if res.get("ok"):
                    n_filled += 1
                else:
                    n_rejected += 1
                details.append({"client_order_id": o["client_order_id"], "result": res})
        return {"ok": True, "open_orders_seen": len(orders), "filled": n_filled, "rejected": n_rejected, "details_sample": details[:20]}

    def mark_to_market(self, venue: str, symbol: str) -> dict:
        q = self._price(venue, symbol)
        m = mid_price(q) if q else None
        cash = self.cash_quote()
        realized = self.realized_pnl()
        pos = self.db.get_position(symbol) or {"qty": 0.0, "avg_price": 0.0, "realized_pnl": 0.0}
        qty = float(pos["qty"])
        avg = float(pos["avg_price"])
        unreal = 0.0
        if m is not None and qty != 0.0:
            unreal = (float(m) - avg) * qty
        equity = cash + (float(m) * qty if m is not None else 0.0)
        self.db.insert_equity(_now(), cash, equity, unreal, realized)
        return {"ok": True, "cash_quote": cash, "equity_quote": equity, "unrealized_pnl": unreal, "realized_pnl": realized, "mid": m}
''')

# 4) Runner (start/stop/status via files; reconciles + MtM loop)
write("services/execution/paper_runner.py", r'''from __future__ import annotations
import json
import os
import time
from datetime import datetime, timezone
from services.admin.config_editor import load_user_yaml
from services.os.app_paths import runtime_dir, ensure_dirs
from services.execution.paper_engine import PaperEngine

FLAGS = runtime_dir() / "flags"
LOCKS = runtime_dir() / "locks"
STOP_FILE = FLAGS / "paper_engine.stop"
LOCK_FILE = LOCKS / "paper_engine.lock"
STATUS_FILE = FLAGS / "paper_engine.status.json"

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _write_status(obj: dict) -> None:
    FLAGS.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def _acquire_lock() -> bool:
    LOCKS.mkdir(parents=True, exist_ok=True)
    if LOCK_FILE.exists():
        return False
    LOCK_FILE.write_text(json.dumps({"pid": os.getpid(), "ts": _now()}, indent=2) + "\n", encoding="utf-8")
    return True

def _release_lock():
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except Exception:
        pass

def request_stop() -> dict:
    ensure_dirs()
    FLAGS.mkdir(parents=True, exist_ok=True)
    STOP_FILE.write_text(_now() + "\n", encoding="utf-8")
    return {"ok": True, "stop_file": str(STOP_FILE)}

def run_forever() -> None:
    ensure_dirs()
    try:
        if STOP_FILE.exists():
            STOP_FILE.unlink()
    except Exception:
        pass
    if not _acquire_lock():
        _write_status({"ok": False, "reason": "lock_exists", "lock_file": str(LOCK_FILE), "ts": _now()})
        return
    eng = PaperEngine()
    cfg = load_user_yaml()
    p = cfg.get("paper_trading") if isinstance(cfg.get("paper_trading"), dict) else {}
    venue = str(p.get("default_venue", "binance") or "binance").lower().strip()
    symbol = str(p.get("default_symbol", "BTC/USDT") or "BTC/USDT").strip()
    interval = float(p.get("loop_interval_sec", 1.0) or 1.0)
    _write_status({"ok": True, "status": "running", "pid": os.getpid(), "venue": venue, "symbol": symbol, "ts": _now()})
    try:
        while True:
            if STOP_FILE.exists():
                _write_status({"ok": True, "status": "stopping", "pid": os.getpid(), "ts": _now()})
                break
            rec = eng.evaluate_open_orders()
            mtm = eng.mark_to_market(venue, symbol)
            _write_status({
                "ok": True,
                "status": "running",
                "pid": os.getpid(),
                "ts": _now(),
                "venue": venue,
                "symbol": symbol,
                "reconcile": {"open_seen": rec.get("open_orders_seen"), "filled": rec.get("filled"), "rejected": rec.get("rejected")},
                "mtm": {"cash": mtm.get("cash_quote"), "equity": mtm.get("equity_quote"), "unreal": mtm.get("unrealized_pnl"), "realized": mtm.get("realized_pnl"), "mid": mtm.get("mid")},
            })
            time.sleep(max(0.25, interval))
    finally:
        _release_lock()
        _write_status({"ok": True, "status": "stopped", "pid": os.getpid(), "ts": _now()})
''')

# 5) CLI run/stop
write("scripts/run_paper_engine.py", r'''#!/usr/bin/env python3
from __future__ import annotations
import argparse
from services.execution.paper_runner import run_forever, request_stop

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run","stop"], nargs="?", default="run")
    args = ap.parse_args()
    if args.cmd == "stop":
        print(request_stop())
        return 0
    run_forever()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
''')

# 6) Dashboard panel (place paper orders + monitor)
def patch_dashboard(t: str) -> str:
    if "Paper Trading Engine v1 (Execution Layer)" in t and "scripts/run_paper_engine.py" in t:
        return t
    add = r'''
st.divider()
st.header("Paper Trading Engine v1 (Execution Layer)")
st.caption("Paper trading only. Idempotent orders (client_order_id unique). Restart-safe reconciliation (open orders are re-evaluated).")
try:
    import json as _json
    import time as _time
    import platform as _platform
    import subprocess as _subprocess
    import sys as _sys
    from pathlib import Path as _Path
    from storage.paper_trading_sqlite import PaperTradingSQLite
    from services.execution.paper_engine import PaperEngine
    db = PaperTradingSQLite()
    eng = PaperEngine()
    status_file = _Path("runtime") / "flags" / "paper_engine.status.json"
    lock_file = _Path("runtime") / "locks" / "paper_engine.lock"
    stop_file = _Path("runtime") / "flags" / "paper_engine.stop"
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Start Paper Engine (background)"):
            cmd = [_sys.executable, "scripts/run_paper_engine.py", "run"]
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
        if st.button("Request stop Paper Engine"):
            stop_file.parent.mkdir(parents=True, exist_ok=True)
            stop_file.write_text(str(int(_time.time())) + "\n", encoding="utf-8")
            st.success({"ok": True, "stop_file": str(stop_file)})
    with c3:
        if st.button("Reconcile now (one-shot)"):
            st.json(eng.evaluate_open_orders())
    st.subheader("Engine status")
    st.caption(f"Lock: {lock_file}")
    if status_file.exists():
        st.json(_json.loads(status_file.read_text(encoding="utf-8")))
    else:
        st.info("No paper engine status file yet.")
    st.subheader("Place a paper order")
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        venue = st.text_input("venue", value="binance")
        symbol = st.text_input("symbol", value="BTC/USDT")
        client_order_id = st.text_input("client_order_id (idempotency key)", value=f"manual_{int(_time.time())}")
    with cc2:
        side = st.selectbox("side", ["buy","sell"], index=0)
        order_type = st.selectbox("order_type", ["market","limit"], index=0)
        qty = st.number_input("qty", min_value=0.0, value=0.001, step=0.001, format="%.6f")
    with cc3:
        limit_price = st.number_input("limit_price (limit only)", min_value=0.0, value=0.0, step=10.0)
        if st.button("Submit order"):
            out = eng.submit_order(
                client_order_id=client_order_id.strip(),
                venue=venue.strip(),
                symbol=symbol.strip(),
                side=side,
                order_type=order_type,
                qty=float(qty),
                limit_price=(float(limit_price) if order_type=="limit" and float(limit_price)>0 else None),
            )
            st.session_state["paper_last_submit"] = out
            st.json(out)
        if st.button("Cancel by client_order_id"):
            out = eng.cancel_order(client_order_id.strip())
            st.session_state["paper_last_cancel"] = out
            st.json(out)
    with st.expander("Last submit/cancel"):
        st.json({"submit": st.session_state.get("paper_last_submit", {}), "cancel": st.session_state.get("paper_last_cancel", {})})
    st.subheader("Positions")
    st.dataframe(db.list_positions(200), use_container_width=True, height=220)
    st.subheader("Orders")
    filt = st.selectbox("filter status", ["(all)","new","filled","canceled","rejected"], index=0)
    orders = db.list_orders(500, status=None if filt=="(all)" else filt)
    st.dataframe(orders, use_container_width=True, height=260)
    st.subheader("Fills")
    st.dataframe(db.list_fills(500), use_container_width=True, height=220)
    st.subheader("Equity (latest 500)")
    eq = db.list_equity(500)
    st.dataframe(eq[:250], use_container_width=True, height=220)
except Exception as e:
    st.error(f"Paper trading panel failed: {type(e).__name__}: {e}")
'''
    return t + "\n" + add

patch("dashboard/app.py", patch_dashboard)

# 7) Config validation for paper_trading.*
def patch_config_editor(t: str) -> str:
    if "paper_trading.enabled" in t and "paper_trading.starting_cash_quote" in t:
        return t
    insert = """
    # Paper trading (optional)
    pt = cfg.get("paper_trading", {})
    if pt is not None and not isinstance(pt, dict):
        errors.append("paper_trading:must_be_mapping")
        pt = {}
    if isinstance(pt, dict):
        if "enabled" in pt and pt["enabled"] is not None and not _is_bool(pt["enabled"]):
            errors.append("paper_trading.enabled:must_be_bool")
        for k in ("starting_cash_quote","fee_bps","slippage_bps","max_order_qty"):
            if k in pt and pt[k] is not None and not _is_float(pt[k]):
                errors.append(f"paper_trading.{k}:must_be_float")
        for k in ("default_venue","default_symbol","quote_currency"):
            if k in pt and pt[k] is not None:
                try:
                    str(pt[k])
                except Exception:
                    errors.append(f"paper_trading.{k}:must_be_string")
        if "loop_interval_sec" in pt and pt["loop_interval_sec"] is not None and not _is_float(pt["loop_interval_sec"]):
            errors.append("paper_trading.loop_interval_sec:must_be_float")
        if "use_ccxt_fallback" in pt and pt["use_ccxt_fallback"] is not None and not _is_bool(pt["use_ccxt_fallback"]):
            errors.append("paper_trading.use_ccxt_fallback:must_be_bool")
"""
    anchor = "ok = len(errors) == 0"
    if anchor in t:
        return t.replace(anchor, insert + "\n" + anchor, 1)
    return t

patch("services/admin/config_editor.py", patch_config_editor)

# 8) Update default config in install.py
def patch_install_py(t: str) -> str:
    if "paper_trading:" in t:
        return t
    marker = "market_data_publisher:\n"
    idx = t.find(marker)
    if idx == -1:
        return t
    yaml_ins = (
        "paper_trading:\n"
        " enabled: true\n"
        " quote_currency: \"USDT\"\n"
        " starting_cash_quote: 10000.0\n"
        " fee_bps: 7.5\n"
        " slippage_bps: 5.0\n"
        " default_venue: \"binance\"\n"
        " default_symbol: \"BTC/USDT\"\n"
        " loop_interval_sec: 1.0\n"
        " use_ccxt_fallback: true\n"
        " max_order_qty: 1000000000.0\n\n"
    )
    return t.replace(marker, yaml_ins + marker, 1)

patch("install.py", patch_install_py)

# 9) CHECKPOINTS
def patch_checkpoints(t: str) -> str:
    if "## DE) Execution Engine v1 (Paper Trading)" in t:
        return t
    return t + (
        "\n## DE) Execution Engine v1 (Paper Trading)\n"
        "- ✅ DE1: SQLite schema for orders/fills/positions/equity + idempotent client_order_id\n"
        "- ✅ DE2: PaperEngine submit/cancel + reconciliation of open orders\n"
        "- ✅ DE3: Market fills use mid + slippage; limit fills cross bid/ask\n"
        "- ✅ DE4: Runner supports start/stop/status via runtime files\n"
        "- ✅ DE5: Dashboard console to place paper orders and monitor positions/orders/fills/equity\n"
    )

patch("CHECKPOINTS.md", patch_checkpoints)

print("OK: Phase 109 applied (paper execution engine + db + runner + dashboard + config validation + checkpoints).")
print("Next steps:")
print("  1. Run paper engine: python3 scripts/run_paper_engine.py run")
print("  2. Check dashboard 'Paper Trading Engine' panel for order placement + monitoring")
print("  3. Test stop: python3 scripts/run_paper_engine.py stop")