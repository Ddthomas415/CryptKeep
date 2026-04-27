from __future__ import annotations
import sqlite3
from services.execution.state_authority import LiveStateContext, update_live_queue_status_as_intent_consumer
import asyncio
import json
import os
import time
from datetime import datetime, timezone
from services.config_loader import load_runtime_trading_config
from services.os.app_paths import runtime_dir, ensure_dirs
from services.risk.market_quality_guard import check as mq_check
from services.market_data.symbol_router import normalize_venue, normalize_symbol
from services.execution.live_arming import is_live_sandbox, live_enabled_and_armed, live_risk_cfg
from services.execution.live_exchange_adapter import LiveExchangeAdapter
from services.live_router.router import decide_order
from storage.live_intent_queue_sqlite import LiveIntentQueueSQLite
from storage.live_trading_sqlite import LiveTradingSQLite
from services.risk.staleness_guard import is_snapshot_fresh
from services.os.file_utils import atomic_write
from services.control.managed_component import clean_stale_lock_file

FLAGS = runtime_dir() / "flags"
LOCKS = runtime_dir() / "locks"
STOP_FILE = FLAGS / "live_intent_consumer.stop"
LOCK_FILE = LOCKS / "live_intent_consumer.lock"
STATUS_FILE = FLAGS / "live_intent_consumer.status.json"

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _write_status(obj: dict) -> None:
    FLAGS.mkdir(parents=True, exist_ok=True)
    atomic_write(STATUS_FILE, json.dumps(obj, indent=2, sort_keys=True) + "\n")

def _acquire_lock() -> bool:
    LOCKS.mkdir(parents=True, exist_ok=True)
    try:
        with open(LOCK_FILE, "x", encoding="utf-8") as fh:
            fh.write(json.dumps({"pid": os.getpid(), "ts": _now()}, indent=2) + "\n")
        return True
    except FileExistsError:
        if clean_stale_lock_file(LOCK_FILE):
            try:
                with open(LOCK_FILE, "x", encoding="utf-8") as fh:
                    fh.write(json.dumps({"pid": os.getpid(), "ts": _now()}, indent=2) + "\n")
                return True
            except FileExistsError:
                return False
        return False

def _release_lock() -> None:
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except Exception as _err:
        pass  # suppressed: live_intent_consumer.py

def request_stop() -> dict:
    ensure_dirs()
    FLAGS.mkdir(parents=True, exist_ok=True)
    atomic_write(STOP_FILE, _now() + "\n")
    return {"ok": True, "stop_file": str(STOP_FILE)}

def _risk_reset_if_needed(db: LiveIntentQueueSQLite) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cur = db.get_state("risk:day") or ""
    if cur != today:
        db.reset_risk_state_for_day(today)

def _risk_check_and_claim(db: LiveIntentQueueSQLite, notional_est: float) -> tuple[bool, str | None]:
    cfg = live_risk_cfg()
    if cfg["min_order_notional_quote"] > 0 and notional_est < cfg["min_order_notional_quote"]:
        return False, "risk:min_order_notional_quote"
    return db.atomic_risk_claim(
        max_trades=int(cfg["max_trades_per_day"]),
        max_notional=float(cfg["max_daily_notional_quote"]),
        notional_est=float(notional_est),
    )


def _live_sandbox_enabled() -> bool:
    try:
        return is_live_sandbox(load_runtime_trading_config())
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        return True


def run_forever() -> None:
    ensure_dirs()
    try:
        if STOP_FILE.exists():
            STOP_FILE.unlink()
    except Exception as _err:
        pass  # suppressed: live_intent_consumer.py
    if not _acquire_lock():
        _write_status({"ok": False, "reason": "lock_exists", "lock_file": str(LOCK_FILE), "ts": _now()})
        return
    qdb = LiveIntentQueueSQLite()
    ldb = LiveTradingSQLite()
    loops = 0
    submitted = 0
    rejected = 0
    _write_status({"ok": True, "status": "running", "pid": os.getpid(), "ts": _now()})
    try:
        while True:
            loops += 1
            if STOP_FILE.exists():
                _write_status({"ok": True, "status": "stopping", "pid": os.getpid(), "ts": _now(), "loops": loops})
                break
            armed, reason = live_enabled_and_armed()
            fresh, stale_reason = is_snapshot_fresh()
            if not armed:
                _write_status({"ok": True, "status": "blocked", "reason": reason, "ts": _now(), "loops": loops})
                time.sleep(1.0)
                continue
            if not fresh:
                _write_status({"ok": True, "status": "blocked", "reason": f"staleness:{stale_reason}", "ts": _now(), "loops": loops})
                time.sleep(1.0)
                continue
            batch = qdb.claim_next_queued(limit=10)
            if not batch:
                _write_status({"ok": True, "status": "running", "ts": _now(), "loops": loops, "queue": 0, "submitted": submitted, "rejected": rejected})
                time.sleep(0.6)
                continue
            sandbox = _live_sandbox_enabled()
            for it in batch:
                ctx = LiveStateContext(authority="INTENT_CONSUMER", origin="live_intent_consumer")
                venue = normalize_venue(it["venue"])
                symbol = normalize_symbol(it["symbol"])
                mq = mq_check(venue, symbol)
                if not mq.get("ok"):
                    _write_status({"ok": True, "status": "running", "ts": _now(), "note": "market_quality_blocked", "blocked": mq, "intent": it.get("intent_id")})
                    continue
                notional_est = float(it["qty"]) * float(it.get("limit_price") or (mq.get("last") or 0.0) or 0.0)
                ok, rreason = _risk_check_and_claim(qdb, notional_est)
                if not ok:
                    update_live_queue_status_as_intent_consumer(qdb, it, "rejected", ctx=ctx, last_error=rreason)
                    rejected += 1
                    continue
                client_order_id = it.get("client_order_id") or f"live_intent_{it['intent_id']}"

                meta = dict(it.get("meta") or {})
                ai_context = {
                    "regime": meta.get("regime"),
                    "volume_surge": meta.get("volume_surge"),
                    "volume_ratio": meta.get("volume_ratio"),
                    "selected_strategy": meta.get("selected_strategy"),
                    "selected_strategy_reason": meta.get("selected_strategy_reason"),
                    "candidate_scores": meta.get("candidate_scores"),
                    "signal_reason": meta.get("signal_reason"),
                }

                decision = asyncio.run(
                    decide_order(
                        venue=venue,
                        symbol_norm=symbol,
                        delta_qty=(float(it["qty"]) if str(it["side"]).lower() == "buy" else -float(it["qty"])),
                        overrides={
                            "reference_price": float(it.get("limit_price") or (mq.get("last") or 0.0) or 0.0),
                            "ai_context": ai_context,
                        },
                    )
                )

                if not bool(decision.allowed):
                    if not update_live_queue_status_as_intent_consumer(qdb, it, "rejected", ctx=ctx, last_error=f"router:{decision.reason}", client_order_id=client_order_id):
                        continue
                    ldb.upsert_order({
                        "client_order_id": client_order_id,
                        "venue": venue,
                        "symbol": symbol,
                        "side": it["side"],
                        "order_type": it["order_type"],
                        "qty": float(it["qty"]),
                        "limit_price": it.get("limit_price"),
                        "exchange_order_id": None,
                        "status": "rejected",
                        "last_error": f"router:{decision.reason}",
                    })
                    rejected += 1
                    continue

                ad = None
                try:
                    ad = LiveExchangeAdapter(venue, sandbox=sandbox)

                    recovered = None
                    try:
                        recovered = ad.find_order_by_client_oid(symbol, client_order_id)
                    except Exception:
                        recovered = None

                    if recovered:
                        ex_oid = str(recovered.get("id") or recovered.get("orderId") or "").strip()
                        if ex_oid:
                            if not update_live_queue_status_as_intent_consumer(
                                qdb,
                                it,
                                "submitted",
                                ctx=ctx,
                                last_error=None,
                                client_order_id=client_order_id,
                                exchange_order_id=ex_oid,
                            ):
                                continue
                            ldb.upsert_order({
                                "client_order_id": client_order_id,
                                "venue": venue,
                                "symbol": symbol,
                                "side": it["side"],
                                "order_type": it["order_type"],
                                "qty": float(it["qty"]),
                                "limit_price": it.get("limit_price"),
                                "exchange_order_id": ex_oid,
                                "status": "submitted",
                                "last_error": None,
                            })
                            submitted += 1
                            continue

                    resp = ad.submit_order(
                        canonical_symbol=symbol,
                        side=decision.side,
                        order_type=decision.order_type,
                        qty=float(decision.qty),
                        limit_price=decision.limit_price,
                        client_order_id=client_order_id,
                    )
                    ex_oid = str(resp.get("id") or resp.get("orderId") or "").strip()
                    if not ex_oid:
                        if not update_live_queue_status_as_intent_consumer(
                            qdb,
                            it,
                            "submit_unknown",
                            ctx=ctx,
                            last_error="submit_response_missing_exchange_order_id",
                            client_order_id=client_order_id,
                        ):
                            continue
                        ldb.upsert_order({
                            "client_order_id": client_order_id,
                            "venue": venue,
                            "symbol": symbol,
                            "side": it["side"],
                            "order_type": it["order_type"],
                            "qty": float(it["qty"]),
                            "limit_price": it.get("limit_price"),
                            "exchange_order_id": None,
                            "status": "submit_unknown",
                            "last_error": "submit_response_missing_exchange_order_id",
                        })
                        continue

                    if not update_live_queue_status_as_intent_consumer(qdb, it, "submitted", ctx=ctx, last_error=None, client_order_id=client_order_id, exchange_order_id=ex_oid):
                        continue
                    ldb.upsert_order({
                        "client_order_id": client_order_id,
                        "venue": venue,
                        "symbol": symbol,
                        "side": it["side"],
                        "order_type": it["order_type"],
                        "qty": float(it["qty"]),
                        "limit_price": it.get("limit_price"),
                        "exchange_order_id": ex_oid,
                        "status": "submitted",
                        "last_error": None,
                    })
                    submitted += 1
                except Exception as e:
                    recovered = None
                    try:
                        recovered = ad.find_order_by_client_oid(symbol, client_order_id) if ad else None
                    except Exception:
                        recovered = None

                    if recovered:
                        ex_oid = str(recovered.get("id") or recovered.get("orderId") or "").strip()
                        if not ex_oid:
                            recovered = None

                    if recovered:
                        if not update_live_queue_status_as_intent_consumer(
                            qdb,
                            it,
                            "submitted",
                            ctx=ctx,
                            last_error=None,
                            client_order_id=client_order_id,
                            exchange_order_id=ex_oid,
                        ):
                            continue
                        ldb.upsert_order({
                            "client_order_id": client_order_id,
                            "venue": venue,
                            "symbol": symbol,
                            "side": it["side"],
                            "order_type": it["order_type"],
                            "qty": float(it["qty"]),
                            "limit_price": it.get("limit_price"),
                            "exchange_order_id": ex_oid,
                            "status": "submitted",
                            "last_error": None,
                        })
                        submitted += 1
                        continue

                    if not update_live_queue_status_as_intent_consumer(qdb, it, "submit_unknown", ctx=ctx, last_error=f"{type(e).__name__}:{e}", client_order_id=client_order_id):
                        continue
                    ldb.upsert_order({
                        "client_order_id": client_order_id,
                        "venue": venue,
                        "symbol": symbol,
                        "side": it["side"],
                        "order_type": it["order_type"],
                        "qty": float(it["qty"]),
                        "limit_price": it.get("limit_price"),
                        "exchange_order_id": None,
                        "status": "submit_unknown",
                        "last_error": f"{type(e).__name__}:{e}",
                    })
                finally:
                    if ad:
                        ad.close()
            _write_status({"ok": True, "status": "running", "ts": _now(), "loops": loops, "submitted": submitted, "rejected": rejected})
            time.sleep(0.4)
    finally:
        _release_lock()
        _write_status({"ok": True, "status": "stopped", "pid": os.getpid(), "ts": _now(), "loops": loops, "submitted": submitted, "rejected": rejected})
