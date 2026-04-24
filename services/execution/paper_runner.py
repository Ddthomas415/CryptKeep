from __future__ import annotations
import json
import logging
import os
import time
from datetime import datetime, timezone
from services.admin.config_editor import load_user_yaml
from services.os.app_paths import runtime_dir, ensure_dirs
from services.execution.intent_reconciler import reconcile_once
from services.execution.paper_engine import PaperEngine
from storage.intent_queue_sqlite import IntentQueueSQLite
from storage.trade_journal_sqlite import TradeJournalSQLite
from services.os.file_utils import atomic_write

FLAGS = runtime_dir() / "flags"
LOCKS = runtime_dir() / "locks"
STOP_FILE = FLAGS / "paper_engine.stop"
LOCK_FILE = LOCKS / "paper_engine.lock"
STATUS_FILE = FLAGS / "paper_engine.status.json"
_LOG = logging.getLogger(__name__)

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _write_status(obj: dict) -> None:
    FLAGS.mkdir(parents=True, exist_ok=True)
    atomic_write(STATUS_FILE, json.dumps(obj, indent=2, sort_keys=True) + "\n")

def _acquire_lock() -> bool:
    LOCKS.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({"pid": os.getpid(), "ts": _now()}, indent=2) + "\n"
    try:
        fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
    except Exception:
        try:
            if LOCK_FILE.exists():
                LOCK_FILE.unlink()
        except Exception:
            pass
        raise
    return True

def _release_lock() -> None:
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except Exception as e:
        _LOG.warning("paper runner lock release failed: %s: %s", type(e).__name__, e)

def request_stop() -> dict:
    ensure_dirs()
    FLAGS.mkdir(parents=True, exist_ok=True)
    atomic_write(STOP_FILE, _now() + "\n")
    return {"ok": True, "stop_file": str(STOP_FILE)}


def _consume_queued_intents_once(*, qdb: IntentQueueSQLite, eng: PaperEngine, limit: int = 20) -> dict:
    queued = qdb.next_queued(limit=int(limit))
    submitted = 0
    rejected = 0
    idempotent = 0
    for it in queued:
        intent_id = str(it.get("intent_id") or "").strip()
        if not intent_id:
            continue
        client_order_id = str(it.get("client_order_id") or f"paper_intent_{intent_id}")
        try:
            resp = eng.submit_order(
                client_order_id=client_order_id,
                venue=str(it.get("venue") or "paper"),
                symbol=str(it.get("symbol") or ""),
                side=str(it.get("side") or ""),
                order_type=str(it.get("order_type") or "market"),
                qty=float(it.get("qty") or 0.0),
                limit_price=(float(it["limit_price"]) if it.get("limit_price") is not None else None),
                ts=str(it.get("ts") or _now()),
                strategy_id=it.get("strategy_id"),
                meta=it.get("meta"),
            )
        except Exception as e:
            qdb.update_status(intent_id, "rejected", last_error=f"{type(e).__name__}:{e}", client_order_id=client_order_id)
            rejected += 1
            continue

        if not bool(resp.get("ok")):
            qdb.update_status(
                intent_id,
                "rejected",
                last_error=str(resp.get("reason") or "paper_submit_failed"),
                client_order_id=client_order_id,
            )
            rejected += 1
            continue

        order = dict(resp.get("order") or {})
        order_id = str(order.get("order_id") or "").strip() or None
        reject_reason = order.get("reject_reason")
        qdb.update_status(
            intent_id,
            "submitted",
            last_error=reject_reason,
            client_order_id=client_order_id,
            linked_order_id=order_id,
        )
        submitted += 1
        if bool(resp.get("idempotent")):
            idempotent += 1

    return {
        "queued_seen": int(len(queued)),
        "submitted": int(submitted),
        "rejected": int(rejected),
        "idempotent": int(idempotent),
    }

def run_forever() -> None:
    ensure_dirs()
    try:
        if STOP_FILE.exists():
            STOP_FILE.unlink()
    except Exception as e:
        _LOG.warning("paper runner stop-file cleanup failed: %s: %s", type(e).__name__, e)
    if not _acquire_lock():
        _write_status({"ok": False, "reason": "lock_exists", "lock_file": str(LOCK_FILE), "ts": _now()})
        return
    eng = PaperEngine()
    qdb = IntentQueueSQLite()
    jdb = TradeJournalSQLite()
    cfg = load_user_yaml()
    p = cfg.get("paper_trading") if isinstance(cfg.get("paper_trading"), dict) else {}
    venue = str((os.environ.get("CBP_VENUE") or p.get("default_venue") or DEFAULT_VENUE)).lower().strip()
    symbols = [x.strip() for x in str(os.environ.get("CBP_SYMBOLS") or "").split(",") if x.strip()]
    if not symbols:
        cfg_symbol = str(p.get("default_symbol", DEFAULT_SYMBOL) or DEFAULT_SYMBOL).strip()
        symbols = [cfg_symbol] if cfg_symbol else [DEFAULT_SYMBOL]
    interval = float(p.get("loop_interval_sec", 1.0) or 1.0)
    max_intents_per_loop = int(p.get("max_intents_per_loop", 20) or 20)
    _write_status({"ok": True, "status": "running", "pid": os.getpid(), "venue": venue, "symbols": symbols, "ts": _now()})
    try:
        while True:
            if STOP_FILE.exists():
                _write_status({"ok": True, "status": "stopping", "pid": os.getpid(), "ts": _now()})
                break
            queue_cycle = _consume_queued_intents_once(qdb=qdb, eng=eng, limit=max_intents_per_loop)
            rec = eng.evaluate_open_orders()
            recon = reconcile_once(qdb=qdb, pdb=eng.db, jdb=jdb, max_intents=max_intents_per_loop)
            mtm_by_symbol = {}
            for symbol in symbols:
                try:
                    mtm_by_symbol[symbol] = eng.mark_to_market(venue, symbol)
                except Exception as e:
                    mtm_by_symbol[symbol] = {"ok": False, "reason": f"{type(e).__name__}:{e}"}

            _write_status({
                "ok": True,
                "status": "running",
                "pid": os.getpid(),
                "ts": _now(),
                "venue": venue,
                "symbols": symbols,
                "queue": queue_cycle,
                "reconcile": {"open_seen": rec.get("open_orders_seen"), "filled": rec.get("filled"), "rejected": rec.get("rejected")},
                "intent_reconcile": recon,
                "mtm": mtm_by_symbol,
            })
            time.sleep(max(0.25, interval))
    finally:
        _release_lock()
        _write_status({"ok": True, "status": "stopped", "pid": os.getpid(), "ts": _now()})


# ---- runtime defaults (prefer env set by bot_ctl / run_bot_safe) ----
DEFAULT_VENUE = (os.environ.get("CBP_VENUE") or "coinbase").lower().strip()
DEFAULT_SYMBOL = "BTC/USD"
