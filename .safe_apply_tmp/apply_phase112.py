# apply_phase112.py - Phase 112 launcher (intent reconciliation + trade journal)
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

# 1) Extend PaperTradingSQLite: get order by order_id + fills for order
def patch_paper_db(t: str) -> str:
    if "def get_order_by_order_id" in t and "def list_fills_for_order" in t:
        return t
    insert = r"""
    def get_order_by_order_id(self, order_id: str) -> Optional[dict]:
        con = _connect()
        try:
            r = con.execute(
                "SELECT order_id, client_order_id, created_ts, ts, venue, symbol, side, order_type, qty, limit_price, status, reject_reason "
                "FROM paper_orders WHERE order_id=?",
                (str(order_id),),
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

    def list_fills_for_order(self, order_id: str, limit: int = 2000) -> list[dict]:
        con = _connect()
        try:
            rows = con.execute(
                "SELECT fill_id, order_id, ts, price, qty, fee, fee_currency FROM paper_fills WHERE order_id=? ORDER BY ts ASC LIMIT ?",
                (str(order_id), int(limit)),
            ).fetchall()
            out = []
            for r in rows:
                out.append({"fill_id": r[0], "order_id": r[1], "ts": r[2], "price": r[3], "qty": r[4], "fee": r[5], "fee_currency": r[6]})
            return out
        finally:
            con.close()
"""
    anchor = " def list_equity"
    if anchor in t:
        return t.replace(anchor, insert + "\n" + anchor, 1)
    return t + "\n" + insert

patch("storage/paper_trading_sqlite.py", patch_paper_db)

# 2) Trade Journal DB
write("storage/trade_journal_sqlite.py", r'''from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from services.os.app_paths import data_dir

DB_PATH = data_dir() / "trade_journal.sqlite"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS journal_fills (
  fill_id TEXT PRIMARY KEY,
  journal_ts TEXT NOT NULL,
  intent_id TEXT,
  source TEXT,
  strategy_id TEXT,
  client_order_id TEXT,
  order_id TEXT NOT NULL,
  fill_ts TEXT NOT NULL,
  venue TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  qty REAL NOT NULL,
  price REAL NOT NULL,
  fee REAL NOT NULL,
  fee_currency TEXT NOT NULL,
  cash_quote REAL,
  pos_qty REAL,
  pos_avg_price REAL,
  realized_pnl_total REAL
);
CREATE INDEX IF NOT EXISTS idx_jf_ts ON journal_fills(journal_ts);
CREATE INDEX IF NOT EXISTS idx_jf_symbol ON journal_fills(symbol);
CREATE INDEX IF NOT EXISTS idx_jf_intent ON journal_fills(intent_id);
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

class TradeJournalSQLite:
    def __init__(self) -> None:
        _connect().close()

    def insert_fill(self, row: dict) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT OR IGNORE INTO journal_fills(fill_id, journal_ts, intent_id, source, strategy_id, client_order_id, order_id, fill_ts, venue, symbol, side, qty, price, fee, fee_currency, cash_quote, pos_qty, pos_avg_price, realized_pnl_total) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    str(row["fill_id"]),
                    str(row.get("journal_ts") or _now()),
                    row.get("intent_id"),
                    row.get("source"),
                    row.get("strategy_id"),
                    row.get("client_order_id"),
                    str(row["order_id"]),
                    str(row["fill_ts"]),
                    str(row["venue"]),
                    str(row["symbol"]),
                    str(row["side"]),
                    float(row["qty"]),
                    float(row["price"]),
                    float(row["fee"]),
                    str(row["fee_currency"]),
                    row.get("cash_quote"),
                    row.get("pos_qty"),
                    row.get("pos_avg_price"),
                    row.get("realized_pnl_total"),
                ),
            )
        finally:
            con.close()

    def list_fills(self, limit: int = 1000) -> list[dict]:
        con = _connect()
        try:
            rows = con.execute(
                "SELECT fill_id, journal_ts, intent_id, source, strategy_id, client_order_id, order_id, fill_ts, venue, symbol, side, qty, price, fee, fee_currency, cash_quote, pos_qty, pos_avg_price, realized_pnl_total "
                "FROM journal_fills ORDER BY journal_ts DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
            out = []
            for r in rows:
                out.append({
                    "fill_id": r[0], "journal_ts": r[1], "intent_id": r[2], "source": r[3], "strategy_id": r[4],
                    "client_order_id": r[5], "order_id": r[6], "fill_ts": r[7], "venue": r[8], "symbol": r[9], "side": r[10],
                    "qty": r[11], "price": r[12], "fee": r[13], "fee_currency": r[14],
                    "cash_quote": r[15], "pos_qty": r[16], "pos_avg_price": r[17], "realized_pnl_total": r[18],
                })
            return out
        finally:
            con.close()

    def count(self) -> int:
        con = _connect()
        try:
            r = con.execute("SELECT COUNT(1) FROM journal_fills").fetchone()
            return int(r[0] if r else 0)
        finally:
            con.close()
''')

# 3) Intent reconciler service
write("services/execution/intent_reconciler.py", r'''from __future__ import annotations
import json
import os
import time
from datetime import datetime, timezone
from services.admin.config_editor import load_user_yaml
from services.os.app_paths import runtime_dir, ensure_dirs
from storage.intent_queue_sqlite import IntentQueueSQLite
from storage.paper_trading_sqlite import PaperTradingSQLite
from storage.trade_journal_sqlite import TradeJournalSQLite

FLAGS = runtime_dir() / "flags"
LOCKS = runtime_dir() / "locks"
STOP_FILE = FLAGS / "intent_reconciler.stop"
LOCK_FILE = LOCKS / "intent_reconciler.lock"
STATUS_FILE = FLAGS / "intent_reconciler.status.json"

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

def _release_lock() -> None:
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

def _cfg() -> dict:
    cfg = load_user_yaml()
    r = cfg.get("intent_reconciler") if isinstance(cfg.get("intent_reconciler"), dict) else {}
    return {
        "enabled": bool(r.get("enabled", True)),
        "poll_interval_sec": float(r.get("poll_interval_sec", 0.8) or 0.8),
        "max_intents_per_loop": int(r.get("max_intents_per_loop", 50) or 50),
    }

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
    pdb = PaperTradingSQLite()
    jdb = TradeJournalSQLite()
    loops = 0
    intents_seen = 0
    intents_updated = 0
    fills_journaled = 0
    _write_status({"ok": True, "status": "running", "pid": os.getpid(), "cfg": cfg, "ts": _now(), "journal_count": jdb.count()})
    try:
        while True:
            loops += 1
            if STOP_FILE.exists():
                _write_status({"ok": True, "status": "stopping", "pid": os.getpid(), "ts": _now(), "loops": loops})
                break
            submitted = qdb.list_intents(limit=int(cfg["max_intents_per_loop"]), status="submitted")
            intents_seen += len(submitted)
            for it in submitted:
                order_id = (it.get("linked_order_id") or "").strip()
                if not order_id:
                    continue
                order = pdb.get_order_by_order_id(order_id)
                if not order:
                    continue
                st = str(order.get("status") or "").lower().strip()
                if st in ("new",):
                    continue
                if st in ("rejected", "canceled"):
                    qdb.update_status(it["intent_id"], st, last_error=order.get("reject_reason"))
                    intents_updated += 1
                    continue
                if st == "filled":
                    qdb.update_status(it["intent_id"], "filled", last_error=None)
                    intents_updated += 1
                    fills = pdb.list_fills_for_order(order_id, limit=5000)
                    pos = pdb.get_position(order["symbol"]) or {"qty": None, "avg_price": None}
                    try:
                        cash = float(pdb.get_state("cash_quote") or "0.0")
                    except Exception:
                        cash = None
                    try:
                        realized = float(pdb.get_state("realized_pnl") or "0.0")
                    except Exception:
                        realized = None
                    for f in fills:
                        jdb.insert_fill({
                            "fill_id": f["fill_id"],
                            "journal_ts": _now(),
                            "intent_id": it.get("intent_id"),
                            "source": it.get("source"),
                            "strategy_id": it.get("strategy_id"),
                            "client_order_id": it.get("client_order_id"),
                            "order_id": order_id,
                            "fill_ts": f["ts"],
                            "venue": order["venue"],
                            "symbol": order["symbol"],
                            "side": order["side"],
                            "qty": f["qty"],
                            "price": f["price"],
                            "fee": f["fee"],
                            "fee_currency": f["fee_currency"],
                            "cash_quote": cash,
                            "pos_qty": pos.get("qty"),
                            "pos_avg_price": pos.get("avg_price"),
                            "realized_pnl_total": realized,
                        })
                        fills_journaled += 1
            _write_status({
                "ok": True,
                "status": "running",
                "pid": os.getpid(),
                "ts": _now(),
                "loops": loops,
                "submitted_checked": len(submitted),
                "intents_seen_total": intents_seen,
                "intents_updated_total": intents_updated,
                "fills_journaled_total": fills_journaled,
                "journal_count": jdb.count(),
            })
            time.sleep(max(0.2, float(cfg["poll_interval_sec"])))
    finally:
        _release_lock()
        _write_status({"ok": True, "status": "stopped", "pid": os.getpid(), "ts": _now(), "loops": loops})
''')

# 4) Runner script
write("scripts/run_intent_reconciler.py", r'''#!/usr/bin/env python3
from __future__ import annotations
import argparse
from services.execution.intent_reconciler import run_forever, request_stop

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
    if "Intent Reconciler + Trade Journal" in t and "scripts/run_intent_reconciler.py" in t:
        return t
    add = r'''
st.divider()
st.header("Intent Reconciler + Trade Journal")
st.caption("Links intents → paper orders/fills. Marks intents filled/rejected/canceled and writes a journal row per fill (idempotent by fill_id).")
try:
    import time as _time
    import platform as _platform
    import subprocess as _subprocess
    import sys as _sys
    import json as _json
    from pathlib import Path as _Path
    from storage.trade_journal_sqlite import TradeJournalSQLite
    from storage.intent_queue_sqlite import IntentQueueSQLite
    jdb = TradeJournalSQLite()
    qdb = IntentQueueSQLite()
    status_file = _Path("runtime") / "flags" / "intent_reconciler.status.json"
    lock_file = _Path("runtime") / "locks" / "intent_reconciler.lock"
    stop_file = _Path("runtime") / "flags" / "intent_reconciler.stop"
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Start Intent Reconciler (background)"):
            cmd = [_sys.executable, "scripts/run_intent_reconciler.py", "run"]
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
        if st.button("Request stop Intent Reconciler"):
            stop_file.parent.mkdir(parents=True, exist_ok=True)
            stop_file.write_text(str(int(_time.time())) + "\n", encoding="utf-8")
            st.success({"ok": True, "stop_file": str(stop_file)})
    with c3:
        if st.button("Show commands"):
            st.code("python3 scripts/run_intent_reconciler.py run\npython3 scripts/run_intent_reconciler.py stop", language="bash")
    st.subheader("Reconciler status")
    st.caption(f"Lock: {lock_file}")
    if status_file.exists():
        st.json(_json.loads(status_file.read_text(encoding="utf-8")))
    else:
        st.info("No reconciler status file yet.")
    st.subheader("Intent status quick view")
    st.dataframe(qdb.list_intents(200, status="submitted"), use_container_width=True, height=180)
    st.subheader("Trade Journal (latest fills)")
    st.caption(f"Total journal rows: {jdb.count()}")
    st.dataframe(jdb.list_fills(500), use_container_width=True, height=320)
except Exception as e:
    st.error(f"Journal panel failed: {type(e).__name__}: {e}")
'''
    return t + "\n" + add

patch("dashboard/app.py", patch_dashboard)

# 6) Config validation
def patch_config_editor(t: str) -> str:
    if "intent_reconciler.enabled" in t and "intent_reconciler.poll_interval_sec" in t:
        return t
    insert = """
    # Intent reconciler (optional)
    ir = cfg.get("intent_reconciler", {})
    if ir is not None and not isinstance(ir, dict):
        errors.append("intent_reconciler:must_be_mapping")
        ir = {}
    if isinstance(ir, dict):
        if "enabled" in ir and ir["enabled"] is not None and not _is_bool(ir["enabled"]):
            errors.append("intent_reconciler.enabled:must_be_bool")
        if "poll_interval_sec" in ir and ir["poll_interval_sec"] is not None and not _is_float(ir["poll_interval_sec"]):
            errors.append("intent_reconciler.poll_interval_sec:must_be_float")
        if "max_intents_per_loop" in ir and ir["max_intents_per_loop"] is not None and not _is_int(ir["max_intents_per_loop"]):
            errors.append("intent_reconciler.max_intents_per_loop:must_be_int")
"""
    anchor = "ok = len(errors) == 0"
    if anchor in t:
        return t.replace(anchor, insert + "\n" + anchor, 1)
    return t

patch("services/admin/config_editor.py", patch_config_editor)

# 7) Default config in install.py
def patch_install_py(t: str) -> str:
    if "intent_reconciler:" in t:
        return t
    marker = "strategy_runner:\n"
    if marker not in t:
        return t
    return t.replace(
        marker,
        "intent_reconciler:\n"
        " enabled: true\n"
        " poll_interval_sec: 0.8\n"
        " max_intents_per_loop: 50\n\n" + marker,
        1
    )

patch("install.py", patch_install_py)

# 8) CHECKPOINTS
def patch_checkpoints(t: str) -> str:
    if "## DH) Intent → Filled + Trade Journal" in t:
        return t
    return t + (
        "\n## DH) Intent → Filled + Trade Journal\n"
        "- ✅ DH1: intent_reconciler watches submitted intents and updates status based on paper order status\n"
        "- ✅ DH2: Writes trade_journal.sqlite journal_fills rows (idempotent by fill_id)\n"
        "- ✅ DH3: Dashboard panel to start/stop reconciler and view journal + submitted intents\n"
        "- ✅ DH4: PaperTradingSQLite extended with get_order_by_order_id + list_fills_for_order\n"
    )

patch("CHECKPOINTS.md", patch_checkpoints)

print("OK: Phase 112 applied (intent reconciliation + trade journal + dashboard + config + checkpoints).")
print("Next steps:")
print("  1. Run reconciler: python3 scripts/run_intent_reconciler.py run")
print("  2. Check dashboard 'Intent Reconciler + Trade Journal' panel")
print("  3. Test stop: python3 scripts/run_intent_reconciler.py stop")