from __future__ import annotations
import json
import os
import sqlite3
import time
from datetime import datetime, timezone
from services.config_loader import load_runtime_trading_config
from services.admin.system_guard import get_state as get_system_guard_state, set_state as set_system_guard_state
from services.os.app_paths import runtime_dir, ensure_dirs
from services.execution.live_arming import is_live_sandbox, live_enabled_and_armed
from services.execution.live_exchange_adapter import LiveExchangeAdapter
from services.execution.state_authority import LiveStateContext, update_live_queue_status_as_reconciler
from services.market_data.symbol_router import normalize_venue, normalize_symbol
from storage.live_intent_queue_sqlite import LiveIntentQueueSQLite
from storage.live_trading_sqlite import LiveTradingSQLite
from services.os.file_utils import atomic_write

FLAGS = runtime_dir() / "flags"
LOCKS = runtime_dir() / "locks"
STOP_FILE = FLAGS / "live_reconciler.stop"
LOCK_FILE = LOCKS / "live_reconciler.lock"
STATUS_FILE = FLAGS / "live_reconciler.status.json"
_RECONCILER_STATE_CONTEXT = LiveStateContext(authority="RECONCILER", origin="live_reconciler")


def _ts_to_ms(v) -> int:
    if v is None:
        return 0
    try:
        if isinstance(v, (int, float)):
            return int(v)
        txt = str(v).strip()
        if not txt:
            return 0
        if txt.isdigit():
            return int(txt)
        dt = datetime.fromisoformat(txt.replace("Z", "+00:00"))
        return int(dt.timestamp() * 1000)
    except (ValueError, TypeError, sqlite3.OperationalError, sqlite3.DatabaseError):
        return 0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_ms() -> int:
    return int(time.time() * 1000)


def _write_status(obj: dict) -> None:
    FLAGS.mkdir(parents=True, exist_ok=True)
    atomic_write(STATUS_FILE, json.dumps(obj, indent=2, sort_keys=True) + "\n")

def _acquire_lock() -> bool:
    LOCKS.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({"pid": os.getpid(), "ts": _now()}, indent=2) + "\n"
    try:
        with open(LOCK_FILE, "x", encoding="utf-8") as fh:
            fh.write(payload)
        return True
    except FileExistsError:
        return False

def _release_lock() -> None:
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except Exception as _err:
        pass  # suppressed: live_reconciler.py

def request_stop() -> dict:
    ensure_dirs()
    FLAGS.mkdir(parents=True, exist_ok=True)
    atomic_write(STOP_FILE, _now() + "\n")
    return {"ok": True, "stop_file": str(STOP_FILE)}


def _live_sandbox_enabled() -> bool:
    try:
        return is_live_sandbox(load_runtime_trading_config())
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        return True


def _adapter_for_reconcile_pass(adapters: dict[str, LiveExchangeAdapter], venue: str, *, sandbox: bool) -> LiveExchangeAdapter:
    ad = adapters.get(venue)
    if ad is None:
        ad = LiveExchangeAdapter(venue, sandbox=bool(sandbox))
        adapters[venue] = ad
    return ad


def _close_reconcile_adapters(adapters: dict[str, LiveExchangeAdapter]) -> None:
    for ad in adapters.values():
        try:
            ad.close()
        except Exception as _err:
            pass  # suppressed: live_reconciler.py
    adapters.clear()


def _system_guard_reconcile_mode() -> tuple[str, dict]:
    state = dict(get_system_guard_state(fail_closed=False) or {})
    guard_state = str(state.get("state") or "").upper().strip()
    if guard_state in {"HALTING", "HALTED"}:
        return "cleanup", state
    return "normal", state


def _maybe_promote_system_guard_halted(qdb: LiveIntentQueueSQLite, guard_meta: dict) -> dict:
    state = str((guard_meta or {}).get("state") or "").upper().strip()
    if state != "HALTING":
        return dict(guard_meta or {})
    try:
        remaining = qdb.list_intents(limit=1, status="submitted")
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        return dict(guard_meta or {})
    if remaining:
        return dict(guard_meta or {})
    try:
        return set_system_guard_state("HALTED", writer="live_reconciler", reason="cleanup_complete")
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        return dict(guard_meta or {})
def _recover_submit_unknown_by_client_order_id(
    *,
    qdb: LiveIntentQueueSQLite,
    ldb: LiveTradingSQLite,
    ad: LiveExchangeAdapter,
    intent: dict,
    venue: str,
    symbol: str,
) -> bool:
    if str(intent.get("status") or "").strip().lower() != "submit_unknown":
        return False
    client_order_id = str(intent.get("client_order_id") or "").strip()
    if not client_order_id:
        return False

    recovered = ad.find_order_by_client_oid(symbol, client_order_id)
    if not recovered:
        return False

    ex_oid = str(recovered.get("id") or recovered.get("orderId") or "").strip()
    if not ex_oid:
        return False

    update_live_queue_status_as_reconciler(
        qdb,
        intent,
        "submitted",
        ctx=_RECONCILER_STATE_CONTEXT,
        last_error=None,
        client_order_id=client_order_id,
        exchange_order_id=ex_oid,
    )
    ldb.upsert_order({
        "client_order_id": client_order_id,
        "venue": venue,
        "symbol": symbol,
        "side": intent["side"],
        "order_type": intent["order_type"],
        "qty": float(intent["qty"]),
        "limit_price": intent.get("limit_price"),
        "exchange_order_id": ex_oid,
        "status": "submitted",
        "last_error": None,
    })
    return True


def run_forever() -> None:
    ensure_dirs()
    try:
        if STOP_FILE.exists():
            STOP_FILE.unlink()
    except Exception as _err:
        pass  # suppressed: live_reconciler.py
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
            reconcile_mode, guard_meta = _system_guard_reconcile_mode()
            guard_state = str(guard_meta.get("state") or "").upper().strip()
            if reconcile_mode == "normal":
                armed, reason = live_enabled_and_armed()
                if not armed:
                    _write_status({
                        "ok": True,
                        "status": "blocked",
                        "reason": reason,
                        "ts": _now(),
                        "loops": loops,
                        "system_guard": guard_meta,
                    })
                    time.sleep(1.0)
                    continue
            submitted = qdb.list_intents(limit=60, status="submitted") + qdb.list_intents(limit=60, status="submit_unknown")
            adapters: dict[str, LiveExchangeAdapter] = {}
            sandbox = _live_sandbox_enabled()
            try:
                for it in submitted:
                    venue = normalize_venue(it["venue"])
                    symbol = normalize_symbol(it["symbol"])
                    ex_oid = (it.get("exchange_order_id") or "").strip()
                    if not ex_oid:
                        if _recover_submit_unknown_by_client_order_id(
                            qdb=qdb,
                            ldb=ldb,
                            ad=_adapter_for_reconcile_pass(adapters, venue, sandbox=sandbox),
                            intent=it,
                            venue=venue,
                            symbol=symbol,
                        ):
                            continue
                        continue
                    try:
                        _submitted_ts_ms = _ts_to_ms(it.get("updated_ts") or it.get("created_ts") or 0)
                        _stale_after_ms = int(os.environ.get("CBP_STALE_ORDER_MS") or "300000")
                        _age_ms = max(0, _now_ms() - _submitted_ts_ms) if _submitted_ts_ms else 0

                        ad = _adapter_for_reconcile_pass(adapters, venue, sandbox=sandbox)
                        if it.get("intent_id") == "drill-stale-001":
                            _write_status({"ok": True, "status": "running", "ts": _now(), "note": "drill6_seen", "intent_id": it.get("intent_id"), "ex_oid": ex_oid, "age_ms": _age_ms, "stale_after_ms": _stale_after_ms})
                        o = ad.fetch_order(symbol, ex_oid)
                        if (not o) and _submitted_ts_ms and _age_ms >= _stale_after_ms:
                            update_live_queue_status_as_reconciler(
                                qdb,
                                it,
                                "error",
                                ctx=_RECONCILER_STATE_CONTEXT,
                                last_error="stale_order_not_found",
                            )
                            ldb.upsert_order({
                                "client_order_id": it.get("client_order_id") or f"live_intent_{it['intent_id']}",
                                "venue": venue, "symbol": symbol, "side": it["side"], "order_type": it["order_type"],
                                "qty": float(it["qty"]), "limit_price": it.get("limit_price"),
                                "exchange_order_id": ex_oid, "status": "error", "last_error": "stale_order_not_found",
                            })
                            continue

                        st = str(o.get("status") or "").lower().strip() or "unknown"
                        if st in ("closed","filled"):
                            update_live_queue_status_as_reconciler(
                                qdb,
                                it,
                                "filled",
                                ctx=_RECONCILER_STATE_CONTEXT,
                                last_error=None,
                            )
                            ldb.upsert_order({
                                "client_order_id": it.get("client_order_id") or f"live_intent_{it['intent_id']}",
                                "venue": venue, "symbol": symbol, "side": it["side"], "order_type": it["order_type"],
                                "qty": float(it["qty"]), "limit_price": it.get("limit_price"),
                                "exchange_order_id": ex_oid, "status": "filled", "last_error": None,
                            })
                        elif st in ("canceled","cancelled"):
                            update_live_queue_status_as_reconciler(
                                qdb,
                                it,
                                "canceled",
                                ctx=_RECONCILER_STATE_CONTEXT,
                                last_error=None,
                            )
                        elif st in ("rejected",):
                            update_live_queue_status_as_reconciler(
                                qdb,
                                it,
                                "rejected",
                                ctx=_RECONCILER_STATE_CONTEXT,
                                last_error=str(o.get("rejectReason") or o.get("info") or "rejected"),
                            )
                        elif st in ("open", "new", "partially_filled", "partiallyfilled"):
                            if _submitted_ts_ms and _age_ms >= _stale_after_ms:
                                update_live_queue_status_as_reconciler(
                                    qdb,
                                    it,
                                    "error",
                                    ctx=_RECONCILER_STATE_CONTEXT,
                                    last_error=f"stale_open_order:{_age_ms}ms",
                                )
                                ldb.upsert_order({
                                    "client_order_id": it.get("client_order_id") or f"live_intent_{it['intent_id']}",
                                    "venue": venue, "symbol": symbol, "side": it["side"], "order_type": it["order_type"],
                                    "qty": float(it["qty"]), "limit_price": it.get("limit_price"),
                                    "exchange_order_id": ex_oid, "status": "error", "last_error": f"stale_open_order:{_age_ms}ms",
                                })
                            else:
                                pass
                        else:
                            pass
                        since_ms = None
                        try:
                            since_ms = int(float(qdb.get_state(f"trades_since_ms:{venue}:{symbol}") or "0")) or None
                        except (sqlite3.OperationalError, sqlite3.DatabaseError):
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
                        _err = f"{type(e).__name__}:{e}"
                        if ex_oid and _submitted_ts_ms and _age_ms >= _stale_after_ms:
                            update_live_queue_status_as_reconciler(
                                qdb,
                                it,
                                "error",
                                ctx=_RECONCILER_STATE_CONTEXT,
                                last_error=f"stale_order_fetch_error:{_err}",
                            )
                            ldb.upsert_order({
                                "client_order_id": it.get("client_order_id") or f"live_intent_{it['intent_id']}",
                                "venue": venue, "symbol": symbol, "side": it["side"], "order_type": it["order_type"],
                                "qty": float(it["qty"]), "limit_price": it.get("limit_price"),
                                "exchange_order_id": ex_oid, "status": "error", "last_error": f"stale_order_fetch_error:{_err}",
                            })
                        _write_status({"ok": True, "status": "running", "ts": _now(), "note": "reconcile_error", "error": _err})
            finally:
                _close_reconcile_adapters(adapters)
            if reconcile_mode == "cleanup":
                guard_meta = _maybe_promote_system_guard_halted(qdb, guard_meta)
                guard_state = str(guard_meta.get("state") or "").upper().strip()
            status_value = guard_state.lower() if reconcile_mode == "cleanup" and guard_state else "running"
            _write_status({
                "ok": True,
                "status": status_value,
                "ts": _now(),
                "loops": loops,
                "fills_seen_total": fills_seen,
                "reconcile_mode": reconcile_mode,
                "system_guard": guard_meta,
            })
            time.sleep(1.5)
    finally:
        _release_lock()
        _write_status({"ok": True, "status": "stopped", "pid": os.getpid(), "ts": _now(), "loops": loops})
