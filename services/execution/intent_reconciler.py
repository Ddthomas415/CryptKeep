from __future__ import annotations
import json
import os
import time
from datetime import datetime, timezone
from services.admin.config_editor import load_user_yaml
from services.os.app_paths import runtime_dir, ensure_dirs
from storage.intent_queue_sqlite import IntentQueueSQLite
from storage.paper_trading_sqlite import PaperTradingSQLite
from storage.trade_journal_sqlite import TradeJournalSQLite
from services.execution.outcome_logger import log_strategy_outcome
from services.os.file_utils import atomic_write

FLAGS = runtime_dir() / "flags"
LOCKS = runtime_dir() / "locks"
STOP_FILE = FLAGS / "intent_reconciler.stop"
LOCK_FILE = LOCKS / "intent_reconciler.lock"
STATUS_FILE = FLAGS / "intent_reconciler.status.json"

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _write_status(obj: dict) -> None:
    FLAGS.mkdir(parents=True, exist_ok=True)
    atomic_write(STATUS_FILE, json.dumps(obj, indent=2, sort_keys=True) + "\n")

def _acquire_lock() -> bool:
    LOCKS.mkdir(parents=True, exist_ok=True)
    if LOCK_FILE.exists():
        return False
    atomic_write(LOCK_FILE, json.dumps({"pid": os.getpid(), "ts": _now()}, indent=2) + "\n")
    return True

def _release_lock() -> None:
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except Exception as _err:
        pass  # suppressed: intent_reconciler.py

def request_stop() -> dict:
    ensure_dirs()
    FLAGS.mkdir(parents=True, exist_ok=True)
    atomic_write(STOP_FILE, _now() + "\n")
    return {"ok": True, "stop_file": str(STOP_FILE)}

def _cfg() -> dict:
    cfg = load_user_yaml()
    r = cfg.get("intent_reconciler") if isinstance(cfg.get("intent_reconciler"), dict) else {}
    return {
        "enabled": bool(r.get("enabled", True)),
        "poll_interval_sec": float(r.get("poll_interval_sec", 0.8) or 0.8),
        "max_intents_per_loop": int(r.get("max_intents_per_loop", 50) or 50),
    }


def reconcile_once(
    *,
    qdb: IntentQueueSQLite | None = None,
    pdb: PaperTradingSQLite | None = None,
    jdb: TradeJournalSQLite | None = None,
    max_intents: int = 50,
) -> dict:
    qdb = qdb or IntentQueueSQLite()
    pdb = pdb or PaperTradingSQLite()
    jdb = jdb or TradeJournalSQLite()
    submitted = qdb.list_intents(limit=int(max_intents), status="submitted")
    intents_updated = 0
    fills_journaled = 0

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
            qdb.update_status(
                it["intent_id"],
                st,
                last_error=order.get("reject_reason"),
                client_order_id=it.get("client_order_id"),
                linked_order_id=order_id,
            )
            intents_updated += 1
            continue
        if st == "filled":
            qdb.update_status(
                it["intent_id"],
                "filled",
                last_error=None,
                client_order_id=it.get("client_order_id"),
                linked_order_id=order_id,
            )
            intents_updated += 1
            fills = pdb.list_fills_for_order(order_id, limit=5000)
            pos = pdb.get_position(order["symbol"]) or {"qty": None, "avg_price": None}
            meta = dict(it.get("meta") or {})
            try:
                cash = float(pdb.get_state("cash_quote") or "0.0")
            except Exception:
                cash = None
            try:
                realized = float(pdb.get_state("realized_pnl") or "0.0")
            except Exception:
                realized = None
            for f in fills:
                journal_row = {
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
                }
                jdb.insert_fill(journal_row)
                log_strategy_outcome({
                    "selected_strategy": meta.get("selected_strategy"),
                    "selected_strategy_reason": meta.get("selected_strategy_reason"),
                    "regime": meta.get("regime"),
                    "volume_surge": meta.get("volume_surge"),
                    "volume_ratio": meta.get("volume_ratio"),
                    "signal_reason": meta.get("signal_reason"),
                    "intent_strategy_id": it.get("strategy_id"),
                    "intent_id": it.get("intent_id"),
                    **journal_row,
                })
                fills_journaled += 1

    return {
        "submitted_checked": int(len(submitted)),
        "intents_updated": int(intents_updated),
        "fills_journaled": int(fills_journaled),
        "journal_count": int(jdb.count()),
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
    except Exception as _err:
        pass  # suppressed: intent_reconciler.py
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
            cycle = reconcile_once(
                qdb=qdb,
                pdb=pdb,
                jdb=jdb,
                max_intents=int(cfg["max_intents_per_loop"]),
            )
            intents_seen += int(cycle.get("submitted_checked") or 0)
            intents_updated += int(cycle.get("intents_updated") or 0)
            fills_journaled += int(cycle.get("fills_journaled") or 0)
            _write_status({
                "ok": True,
                "status": "running",
                "pid": os.getpid(),
                "ts": _now(),
                "loops": loops,
                "submitted_checked": int(cycle.get("submitted_checked") or 0),
                "intents_seen_total": intents_seen,
                "intents_updated_total": intents_updated,
                "fills_journaled_total": fills_journaled,
                "journal_count": int(cycle.get("journal_count") or 0),
            })
            time.sleep(max(0.2, float(cfg["poll_interval_sec"])))
    finally:
        _release_lock()
        _write_status({"ok": True, "status": "stopped", "pid": os.getpid(), "ts": _now(), "loops": loops})
