from __future__ import annotations
import json
import os
import time
from datetime import datetime, timezone
from services.os.app_paths import runtime_dir, ensure_dirs
from services.execution.live_arming import live_enabled_and_armed
from services.execution.live_exchange_adapter import LiveExchangeAdapter
from services.market_data.symbol_router import normalize_venue, normalize_symbol
from storage.live_intent_queue_sqlite import LiveIntentQueueSQLite
from storage.live_trading_sqlite import LiveTradingSQLite

FLAGS = runtime_dir() / "flags"
LOCKS = runtime_dir() / "locks"
STOP_FILE = FLAGS / "live_reconciler.stop"
LOCK_FILE = LOCKS / "live_reconciler.lock"
STATUS_FILE = FLAGS / "live_reconciler.status.json"

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


def _adapter_for_reconcile_pass(adapters: dict[str, LiveExchangeAdapter], venue: str) -> LiveExchangeAdapter:
    ad = adapters.get(venue)
    if ad is None:
        ad = LiveExchangeAdapter(venue)
        adapters[venue] = ad
    return ad


def _close_reconcile_adapters(adapters: dict[str, LiveExchangeAdapter]) -> None:
    for ad in adapters.values():
        try:
            ad.close()
        except Exception:
            pass
    adapters.clear()

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
    qdb = LiveIntentQueueSQLite()
    ldb = LiveTradingSQLite()
    loops = 0
    fills_seen = 0
    _write_status({"ok": True, "status": "running", "pid": os.getpid(), "ts": _now()})
    try:
        while True:
            loops += 1
            if STOP_FILE.exists():
                _write_status({"ok": True, "status": "stopping", "ts": _now(), "loops": loops})
                break
            armed, reason = live_enabled_and_armed()
            if not armed:
                _write_status({"ok": True, "status": "blocked", "reason": reason, "ts": _now(), "loops": loops})
                time.sleep(1.0)
                continue
            submitted = qdb.list_intents(limit=60, status="submitted")
            adapters: dict[str, LiveExchangeAdapter] = {}
            try:
                for it in submitted:
                    venue = normalize_venue(it["venue"])
                    symbol = normalize_symbol(it["symbol"])
                    ex_oid = (it.get("exchange_order_id") or "").strip()
                    if not ex_oid:
                        continue
                    try:
                        ad = _adapter_for_reconcile_pass(adapters, venue)
                        o = ad.fetch_order(symbol, ex_oid)
                        st = str(o.get("status") or "").lower().strip() or "unknown"
                        if st in ("closed","filled"):
                            qdb.update_status(it["intent_id"], "filled", last_error=None)
                            ldb.upsert_order({
                                "client_order_id": it.get("client_order_id") or f"live_intent_{it['intent_id']}",
                                "venue": venue, "symbol": symbol, "side": it["side"], "order_type": it["order_type"],
                                "qty": float(it["qty"]), "limit_price": it.get("limit_price"),
                                "exchange_order_id": ex_oid, "status": "filled", "last_error": None,
                            })
                        elif st in ("canceled","cancelled"):
                            qdb.update_status(it["intent_id"], "canceled", last_error=None)
                        elif st in ("rejected",):
                            qdb.update_status(it["intent_id"], "rejected", last_error=str(o.get("rejectReason") or o.get("info") or "rejected"))
                        else:
                            pass
                        since_ms = None
                        try:
                            since_ms = int(float(qdb.get_state(f"trades_since_ms:{venue}:{symbol}") or "0")) or None
                        except Exception:
                            since_ms = None
                        trades = ad.fetch_my_trades(symbol, since_ms=since_ms, limit=200)
                        max_ts = 0
                        for tr in trades or []:
                            tid = str(tr.get("id") or tr.get("tradeId") or "")
                            ts = tr.get("timestamp")
                            if ts:
                                max_ts = max(max_ts, int(ts))
                            if not tid:
                                continue
                            ldb.insert_fill({
                                "trade_id": tid,
                                "ts": str(tr.get("datetime") or _now()),
                                "venue": venue,
                                "symbol": symbol,
                                "side": str(tr.get("side") or it["side"]).lower(),
                                "qty": float(tr.get("amount") or tr.get("qty") or 0.0),
                                "price": float(tr.get("price") or 0.0),
                                "fee": (tr.get("fee") or {}).get("cost") if isinstance(tr.get("fee"), dict) else None,
                                "fee_currency": (tr.get("fee") or {}).get("currency") if isinstance(tr.get("fee"), dict) else None,
                                "client_order_id": it.get("client_order_id"),
                                "exchange_order_id": ex_oid,
                            })
                            fills_seen += 1
                        if max_ts:
                            qdb.set_state(f"trades_since_ms:{venue}:{symbol}", str(max_ts + 1))
                    except Exception as e:
                        _write_status({"ok": True, "status": "running", "ts": _now(), "note": "reconcile_error", "error": f"{type(e).__name__}:{e}"})
            finally:
                _close_reconcile_adapters(adapters)
            _write_status({"ok": True, "status": "running", "ts": _now(), "loops": loops, "fills_seen_total": fills_seen})
            time.sleep(1.5)
    finally:
        _release_lock()
        _write_status({"ok": True, "status": "stopped", "pid": os.getpid(), "ts": _now(), "loops": loops})
