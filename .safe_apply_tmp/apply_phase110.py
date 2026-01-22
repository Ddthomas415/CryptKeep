# apply_phase110.py - Phase 110 launcher (intent queue + consumer + UI)
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

# 1) Intent Queue DB
write("storage/intent_queue_sqlite.py", r'''from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from services.os.app_paths import data_dir

DB_PATH = data_dir() / "intent_queue.sqlite"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS trade_intents (
  intent_id TEXT PRIMARY KEY,
  created_ts TEXT NOT NULL,
  ts TEXT NOT NULL,
  source TEXT NOT NULL,
  strategy_id TEXT,
  venue TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  order_type TEXT NOT NULL,
  qty REAL NOT NULL,
  limit_price REAL,
  status TEXT NOT NULL,
  last_error TEXT,
  client_order_id TEXT,
  linked_order_id TEXT,
  updated_ts TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ti_status_ts ON trade_intents(status, created_ts);
CREATE INDEX IF NOT EXISTS idx_ti_symbol_ts ON trade_intents(symbol, ts);
CREATE TABLE IF NOT EXISTS consumer_state (
  k TEXT PRIMARY KEY,
  v TEXT NOT NULL
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

class IntentQueueSQLite:
    def __init__(self) -> None:
        _connect().close()

    def upsert_intent(self, row: Dict[str, Any]) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO trade_intents(intent_id, created_ts, ts, source, strategy_id, venue, symbol, side, order_type, qty, limit_price, status, last_error, client_order_id, linked_order_id, updated_ts) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    str(row["intent_id"]),
                    str(row.get("created_ts") or _now()),
                    str(row["ts"]),
                    str(row["source"]),
                    row.get("strategy_id"),
                    str(row["venue"]),
                    str(row["symbol"]),
                    str(row["side"]),
                    str(row["order_type"]),
                    float(row["qty"]),
                    row.get("limit_price"),
                    str(row["status"]),
                    row.get("last_error"),
                    row.get("client_order_id"),
                    row.get("linked_order_id"),
                    _now(),
                ),
            )
        finally:
            con.close()

    def get_intent(self, intent_id: str) -> Optional[Dict[str, Any]]:
        con = _connect()
        try:
            r = con.execute(
                "SELECT intent_id, created_ts, ts, source, strategy_id, venue, symbol, side, order_type, qty, limit_price, status, last_error, client_order_id, linked_order_id, updated_ts "
                "FROM trade_intents WHERE intent_id=?",
                (str(intent_id),),
            ).fetchone()
            if not r:
                return None
            return {
                "intent_id": r[0], "created_ts": r[1], "ts": r[2], "source": r[3], "strategy_id": r[4],
                "venue": r[5], "symbol": r[6], "side": r[7], "order_type": r[8], "qty": r[9], "limit_price": r[10],
                "status": r[11], "last_error": r[12], "client_order_id": r[13], "linked_order_id": r[14], "updated_ts": r[15],
            }
        finally:
            con.close()

    def list_intents(self, limit: int = 500, status: str | None = None) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            q = ("SELECT intent_id, created_ts, ts, source, strategy_id, venue, symbol, side, order_type, qty, limit_price, status, last_error, client_order_id, linked_order_id, updated_ts "
                 "FROM trade_intents")
            args = []
            if status:
                q += " WHERE status=?"
                args.append(str(status))
            q += " ORDER BY created_ts DESC LIMIT ?"
            args.append(int(limit))
            rows = con.execute(q, tuple(args)).fetchall()
            return [
                {
                    "intent_id": r[0], "created_ts": r[1], "ts": r[2], "source": r[3], "strategy_id": r[4],
                    "venue": r[5], "symbol": r[6], "side": r[7], "order_type": r[8], "qty": r[9], "limit_price": r[10],
                    "status": r[11], "last_error": r[12], "client_order_id": r[13], "linked_order_id": r[14], "updated_ts": r[15],
                }
                for r in rows
            ]
        finally:
            con.close()

    def next_queued(self, limit: int = 20) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            rows = con.execute(
                ("SELECT intent_id, created_ts, ts, source, strategy_id, venue, symbol, side, order_type, qty, limit_price, status, last_error, client_order_id, linked_order_id, updated_ts "
                 "FROM trade_intents WHERE status='queued' ORDER BY created_ts ASC LIMIT ?"),
                (int(limit),),
            ).fetchall()
            return [
                {
                    "intent_id": r[0], "created_ts": r[1], "ts": r[2], "source": r[3], "strategy_id": r[4],
                    "venue": r[5], "symbol": r[6], "side": r[7], "order_type": r[8], "qty": r[9], "limit_price": r[10],
                    "status": r[11], "last_error": r[12], "client_order_id": r[13], "linked_order_id": r[14], "updated_ts": r[15],
                }
                for r in rows
            ]
        finally:
            con.close()

    def update_status(self, intent_id: str, status: str, *, last_error: str | None = None, client_order_id: str | None = None, linked_order_id: str | None = None) -> None:
        con = _connect()
        try:
            con.execute(
                "UPDATE trade_intents SET status=?, last_error=?, client_order_id=?, linked_order_id=?, updated_ts=? WHERE intent_id=?",
                (str(status), last_error, client_order_id, linked_order_id, _now(), str(intent_id)),
            )
        finally:
            con.close()

    def get_state(self, k: str) -> Optional[str]:
        con = _connect()
        try:
            r = con.execute("SELECT v FROM consumer_state WHERE k=?", (str(k),)).fetchone()
            return r[0] if r else None
        finally:
            con.close()

    def set_state(self, k: str, v: str) -> None:
        con = _connect()
        try:
            con.execute("INSERT OR REPLACE INTO consumer_state(k,v) VALUES(?,?)", (str(k), str(v)))
        finally:
            con.close()
''')

# 2) Intent model + helpers
write("services/strategy/trade_intent.py", r'''from __future__ import annotations
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass(frozen=True)
class TradeIntent:
    intent_id: str
    ts: str
    source: str  # manual|strategy|evidence
    strategy_id: str | None
    venue: str
    symbol: str
    side: str  # buy|sell
    order_type: str  # market|limit
    qty: float
    limit_price: float | None = None

    @staticmethod
    def manual(*, venue: str, symbol: str, side: str, order_type: str, qty: float, limit_price: float | None = None) -> "TradeIntent":
        return TradeIntent(
            intent_id=str(uuid.uuid4()),
            ts=now_iso(),
            source="manual",
            strategy_id=None,
            venue=str(venue).lower().strip(),
            symbol=str(symbol).strip(),
            side=str(side).lower().strip(),
            order_type=str(order_type).lower().strip(),
            qty=float(qty),
            limit_price=(float(limit_price) if limit_price is not None else None),
        )
''')

# 3) Consumer: queued intents -> PaperEngine submit (idempotent), cooldown, minimal risk gate
write("services/execution/intent_consumer.py", r'''from __future__ import annotations
import json
import time
from datetime import datetime, timezone
from typing import Optional
from services.admin.config_editor import load_user_yaml
from services.execution.paper_engine import PaperEngine
from services.os.app_paths import runtime_dir, ensure_dirs
from storage.intent_queue_sqlite import IntentQueueSQLite

FLAGS = runtime_dir() / "flags"
LOCKS = runtime_dir() / "locks"
STOP_FILE = FLAGS / "intent_consumer.stop"
LOCK_FILE = LOCKS / "intent_consumer.lock"
STATUS_FILE = FLAGS / "intent_consumer.status.json"

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

def _cfg() -> dict:
    cfg = load_user_yaml()
    c = cfg.get("intent_consumer") if isinstance(cfg.get("intent_consumer"), dict) else {}
    return {
        "enabled": bool(c.get("enabled", True)),
        "poll_interval_sec": float(c.get("poll_interval_sec", 0.8) or 0.8),
        "max_per_loop": int(c.get("max_per_loop", 10) or 10),
        "cooldown_sec": float(c.get("cooldown_sec", 5.0) or 5.0),
        "cooldown_key": str(c.get("cooldown_key", "symbol_side") or "symbol_side"),
        "risk_gate_enabled": bool(c.get("risk_gate_enabled", True)),
        "max_trades_per_day": int(c.get("max_trades_per_day", 0) or 0),
        "max_daily_notional_quote": float(c.get("max_daily_notional_quote", 0.0) or 0.0),
    }

def request_stop() -> dict:
    ensure_dirs()
    FLAGS.mkdir(parents=True, exist_ok=True)
    STOP_FILE.write_text(_now() + "\n", encoding="utf-8")
    return {"ok": True, "stop_file": str(STOP_FILE)}

def _cooldown_key(cfg: dict, venue: str, symbol: str, side: str) -> str:
    if cfg["cooldown_key"] == "symbol":
        return f"{venue}:{symbol}"
    return f"{venue}:{symbol}:{side}"

def _cooldown_ok(db: IntentQueueSQLite, key: str, cooldown_sec: float) -> bool:
    v = db.get_state(f"cooldown:{key}") or ""
    try:
        last = float(v)
    except Exception:
        last = 0.0
    return (time.time() - last) >= float(cooldown_sec)

def _cooldown_mark(db: IntentQueueSQLite, key: str) -> None:
    db.set_state(f"cooldown:{key}", str(time.time()))

def _risk_gate_ok(cfg: dict, db: IntentQueueSQLite, intent: dict) -> tuple[bool, str | None]:
    if not bool(cfg["risk_gate_enabled"]):
        return True, None
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cur_day = db.get_state("risk:day") or ""
    if cur_day != today:
        db.set_state("risk:day", today)
        db.set_state("risk:trades", "0")
        db.set_state("risk:notional", "0.0")
    trades = int(float(db.get_state("risk:trades") or "0"))
    notional = float(db.get_state("risk:notional") or "0.0")
    max_trades = int(cfg["max_trades_per_day"])
    if max_trades > 0 and trades >= max_trades:
        return False, "risk:max_trades_per_day"
    max_notional = float(cfg["max_daily_notional_quote"])
    if max_notional > 0 and notional >= max_notional:
        return False, "risk:max_daily_notional_quote"
    return True, None

def _risk_gate_commit(db: IntentQueueSQLite, approx_notional: float) -> None:
    trades = int(float(db.get_state("risk:trades") or "0"))
    notional = float(db.get_state("risk:notional") or "0.0")
    db.set_state("risk:trades", str(trades + 1))
    db.set_state("risk:notional", str(notional + float(approx_notional)))

def run_forever() -> None:
    ensure_dirs()
    cfg = _cfg()
    if not bool(cfg["enabled"]):
        _write_status({"ok": False, "reason": "disabled", "ts": _now()})
        return
    try:
        if STOP_FILE.exists():
            STOP_FILE.unlink()
    except Exception:
        pass
    if not _acquire_lock():
        _write_status({"ok": False, "reason": "lock_exists", "lock_file": str(LOCK_FILE), "ts": _now()})
        return
    qdb = IntentQueueSQLite()
    eng = PaperEngine()
    _write_status({"ok": True, "status": "running", "ts": _now(), "cfg": cfg})
    processed = 0
    submitted = 0
    rejected = 0
    try:
        while True:
            if STOP_FILE.exists():
                _write_status({"ok": True, "status": "stopping", "ts": _now(), "processed": processed, "submitted": submitted, "rejected": rejected})
                break
            batch = qdb.next_queued(limit=int(cfg["max_per_loop"]))
            if not batch:
                _write_status({"ok": True, "status": "running", "ts": _now(), "queue": 0, "processed": processed, "submitted": submitted, "rejected": rejected})
                time.sleep(max(0.2, float(cfg["poll_interval_sec"])))
                continue
            for it in batch:
                processed += 1
                key = _cooldown_key(cfg, it["venue"], it["symbol"], it["side"])
                if not _cooldown_ok(qdb, key, float(cfg["cooldown_sec"])):
                    continue
                ok, reason = _risk_gate_ok(cfg, qdb, it)
                if not ok:
                    qdb.update_status(it["intent_id"], "rejected", last_error=reason)
                    rejected += 1
                    _cooldown_mark(qdb, key)
                    continue
                client_order_id = f"intent_{it['intent_id']}"
                out = eng.submit_order(
                    client_order_id=client_order_id,
                    venue=it["venue"],
                    symbol=it["symbol"],
                    side=it["side"],
                    order_type=it["order_type"],
                    qty=float(it["qty"]),
                    limit_price=(float(it["limit_price"]) if it.get("limit_price") is not None else None),
                    ts=it["ts"],
                )
                if not out.get("ok"):
                    qdb.update_status(it["intent_id"], "rejected", last_error=str(out.get("reason") or "submit_failed"), client_order_id=client_order_id)
                    rejected += 1
                    _cooldown_mark(qdb, key)
                    continue
                order = (out.get("order") or {})
                qdb.update_status(
                    it["intent_id"],
                    "submitted",
                    last_error=None,
                    client_order_id=client_order_id,
                    linked_order_id=str(order.get("order_id") or ""),
                )
                submitted += 1
                approx_notional = float(it["qty"]) * float(it.get("limit_price") or 0.0)
                _risk_gate_commit(qdb, approx_notional)
                _cooldown_mark(qdb, key)
            _write_status({"ok": True, "status": "running", "ts": _now(), "queue": len(batch), "processed": processed, "submitted": submitted, "rejected": rejected})
            time.sleep(max(0.2, float(cfg["poll_interval_sec"])))
    finally:
        _release_lock()
        _write_status({"ok": True, "status": "stopped", "ts": _now(), "processed": processed, "submitted": submitted, "rejected": rejected})
''')

# 4) Runner script
write("scripts/run_intent_consumer.py", r'''#!/usr/bin/env python3
from __future__ import annotations
import argparse
from services.execution.intent_consumer import run_forever, request_stop

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

# 5) Dashboard panel
def patch_dashboard(t: str) -> str:
    if "Strategy → Intent Queue (v1)" in t and "scripts/run_intent_consumer.py" in t:
        return t
    add = r'''
st.divider()
st.header("Strategy → Intent Queue (v1)")
st.caption("Create trade intents (manual/strategy). Consumer submits them to Paper Engine with idempotent client_order_id=intent_<intent_id>, cooldowns, and a minimal risk gate.")
try:
    import time as _time
    import platform as _platform
    import subprocess as _subprocess
    import sys as _sys
    import json as _json
    from pathlib import Path as _Path
    from services.strategy.trade_intent import TradeIntent
    from storage.intent_queue_sqlite import IntentQueueSQLite
    qdb = IntentQueueSQLite()
    status_file = _Path("runtime") / "flags" / "intent_consumer.status.json"
    lock_file = _Path("runtime") / "locks" / "intent_consumer.lock"
    stop_file = _Path("runtime") / "flags" / "intent_consumer.stop"
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Start Intent Consumer (background)"):
            cmd = [_sys.executable, "scripts/run_intent_consumer.py", "run"]
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
        if st.button("Request stop Intent Consumer"):
            stop_file.parent.mkdir(parents=True, exist_ok=True)
            stop_file.write_text(str(int(_time.time())) + "\n", encoding="utf-8")
            st.success({"ok": True, "stop_file": str(stop_file)})
    with c3:
        if st.button("Refresh consumer status"):
            pass
    st.subheader("Consumer status")
    st.caption(f"Lock: {lock_file}")
    if status_file.exists():
        st.json(_json.loads(status_file.read_text(encoding="utf-8")))
    else:
        st.info("No consumer status file yet.")
    st.subheader("Create manual intent")
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        venue = st.text_input("intent venue", value="binance")
        symbol = st.text_input("intent symbol", value="BTC/USDT")
    with cc2:
        side = st.selectbox("intent side", ["buy","sell"], index=0)
        order_type = st.selectbox("intent order_type", ["market","limit"], index=0)
        qty = st.number_input("intent qty", min_value=0.0, value=0.001, step=0.001, format="%.6f")
    with cc3:
        limit_price = st.number_input("intent limit_price (limit only)", min_value=0.0, value=0.0, step=10.0)
        if st.button("Enqueue intent"):
            it = TradeIntent.manual(
                venue=venue.strip(),
                symbol=symbol.strip(),
                side=side,
                order_type=order_type,
                qty=float(qty),
                limit_price=(float(limit_price) if order_type=="limit" and float(limit_price)>0 else None),
            )
            qdb.upsert_intent({
                "intent_id": it.intent_id,
                "created_ts": it.ts,
                "ts": it.ts,
                "source": it.source,
                "strategy_id": it.strategy_id,
                "venue": it.venue,
                "symbol": it.symbol,
                "side": it.side,
                "order_type": it.order_type,
                "qty": it.qty,
                "limit_price": it.limit_price,
                "status": "queued",
                "last_error": None,
                "client_order_id": None,
                "linked_order_id": None,
            })
            st.success({"ok": True, "intent_id": it.intent_id})
        if st.button("Enqueue 5 demo intents (alternating buy/sell)"):
            for i in range(5):
                s = "buy" if i % 2 == 0 else "sell"
                it = TradeIntent.manual(venue=venue.strip(), symbol=symbol.strip(), side=s, order_type="market", qty=float(qty))
                qdb.upsert_intent({
                    "intent_id": it.intent_id, "created_ts": it.ts, "ts": it.ts, "source": it.source, "strategy_id": it.strategy_id,
                    "venue": it.venue, "symbol": it.symbol, "side": it.side, "order_type": it.order_type, "qty": it.qty, "limit_price": None,
                    "status": "queued", "last_error": None, "client_order_id": None, "linked_order_id": None,
                })
            st.success({"ok": True, "enqueued": 5})
    st.subheader("Queue")
    filt = st.selectbox("intent filter status", ["(all)","queued","submitted","filled","rejected","canceled"], index=0)
    intents = qdb.list_intents(500, status=None if filt=="(all)" else filt)
    st.dataframe(intents, use_container_width=True, height=320)
except Exception as e:
    st.error(f"Intent queue panel failed: {type(e).__name__}: {e}")
'''
    return t + "\n" + add

patch("dashboard/app.py", patch_dashboard)

# 6) Config validation
def patch_config_editor(t: str) -> str:
    if "intent_consumer.enabled" in t and "intent_consumer.cooldown_sec" in t:
        return t
    insert = """
    # Intent consumer (optional)
    ic = cfg.get("intent_consumer", {})
    if ic is not None and not isinstance(ic, dict):
        errors.append("intent_consumer:must_be_mapping")
        ic = {}
    if isinstance(ic, dict):
        if "enabled" in ic and ic["enabled"] is not None and not _is_bool(ic["enabled"]):
            errors.append("intent_consumer.enabled:must_be_bool")
        for k in ("poll_interval_sec","cooldown_sec","max_daily_notional_quote"):
            if k in ic and ic[k] is not None and not _is_float(ic[k]):
                errors.append(f"intent_consumer.{k}:must_be_float")
        for k in ("max_per_loop","max_trades_per_day"):
            if k in ic and ic[k] is not None and not _is_int(ic[k]):
                errors.append(f"intent_consumer.{k}:must_be_int")
        if "cooldown_key" in ic and ic["cooldown_key"] is not None:
            try:
                str(ic["cooldown_key"])
            except Exception:
                errors.append("intent_consumer.cooldown_key:must_be_string")
        if "risk_gate_enabled" in ic and ic["risk_gate_enabled"] is not None and not _is_bool(ic["risk_gate_enabled"]):
            errors.append("intent_consumer.risk_gate_enabled:must_be_bool")
"""
    anchor = "ok = len(errors) == 0"
    if anchor in t:
        return t.replace(anchor, insert + "\n" + anchor, 1)
    return t

patch("services/admin/config_editor.py", patch_config_editor)

# 7) Default config in install.py
def patch_install_py(t: str) -> str:
    if "intent_consumer:" in t:
        return t
    marker = "paper_trading:\n"
    if marker not in t:
        return t
    return t.replace(
        marker,
        marker + (
            "intent_consumer:\n"
            " enabled: true\n"
            " poll_interval_sec: 0.8\n"
            " max_per_loop: 10\n"
            " cooldown_sec: 5.0\n"
            " cooldown_key: \"symbol_side\"\n"
            " risk_gate_enabled: true\n"
            " max_trades_per_day: 0\n"
            " max_daily_notional_quote: 0.0\n\n"
        ),
        1
    )

patch("install.py", patch_install_py)

# 8) CHECKPOINTS
def patch_checkpoints(t: str) -> str:
    if "## DF) Strategy → Intent Pipeline (Paper)" in t:
        return t
    return t + (
        "\n## DF) Strategy → Intent Pipeline (Paper)\n"
        "- ✅ DF1: intent_queue.sqlite trade_intents table with durable statuses\n"
        "- ✅ DF2: Intent consumer submits queued intents to PaperEngine using client_order_id=intent_<intent_id>\n"
        "- ✅ DF3: Cooldown per symbol or symbol+side to prevent rapid repeats\n"
        "- ✅ DF4: Minimal risk gate (max_trades/day, max_daily_notional_quote) using consumer_state counters\n"
        "- ✅ DF5: Dashboard panel to enqueue intents + start/stop consumer + inspect queue\n"
    )

patch("CHECKPOINTS.md", patch_checkpoints)

print("OK: Phase 110 applied (intent queue + consumer + UI + config validation + checkpoints).")
print("Next steps:")
print("  1. Run intent consumer: python3 scripts/run_intent_consumer.py run")
print("  2. Check dashboard 'Strategy → Intent Queue' panel for enqueue + monitoring")
print("  3. Test stop: python3 scripts/run_intent_consumer.py stop")