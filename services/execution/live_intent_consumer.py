from __future__ import annotations
import logging
import sqlite3
from services.execution.state_authority import LiveStateContext, update_live_queue_status_as_intent_consumer
import asyncio
import json
import math
import os
import time
from datetime import datetime, timezone
from services.config_loader import load_runtime_trading_config
from services.os.app_paths import runtime_dir, ensure_dirs
from services.risk.market_quality_guard import check as mq_check
from services.market_data.symbol_router import normalize_venue, normalize_symbol
from services.execution.live_arming import is_live_sandbox, live_enabled_and_armed, live_risk_cfg
from services.execution.intent_ttl import check_intent_age
from services.execution.clock_sanity import check_venue_clock
from services.process.heartbeat import write_named_heartbeat
from services.execution.live_exchange_adapter import LiveExchangeAdapter
from services.live_router.router import decide_order
from storage.live_intent_queue_sqlite import LiveIntentQueueSQLite
from storage.live_trading_sqlite import LiveTradingSQLite
from storage.order_dedupe_store_sqlite import OrderDedupeStore
from services.risk.staleness_guard import is_snapshot_fresh
from services.os.file_utils import atomic_write
from services.control.managed_component import clean_stale_lock_file

FLAGS = runtime_dir() / "flags"
LOCKS = runtime_dir() / "locks"
STOP_FILE = FLAGS / "live_intent_consumer.stop"
LOCK_FILE = LOCKS / "live_intent_consumer.lock"
STATUS_FILE = FLAGS / "live_intent_consumer.status.json"
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
        if not clean_stale_lock_file(LOCK_FILE):
            return False
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
    _risk_reset_if_needed(db)
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


SUBMITTING_STALE_RECOVERY_MS_ENV = "CBP_SUBMITTING_STALE_RECOVERY_MS"
SUBMITTING_STALE_RECOVERY_MS_DEFAULT = 120_000.0


def _submitting_stale_recovery_ms() -> float:
    """Age threshold for the startup recovery sweep. Invalid, non-finite, or
    non-positive env overrides fall back to the strict default."""
    raw = os.environ.get(SUBMITTING_STALE_RECOVERY_MS_ENV)
    if raw is None or str(raw).strip() == "":
        return SUBMITTING_STALE_RECOVERY_MS_DEFAULT
    try:
        value = float(raw)
    except Exception as _err:
        return SUBMITTING_STALE_RECOVERY_MS_DEFAULT
    if not math.isfinite(value) or value <= 0.0:
        return SUBMITTING_STALE_RECOVERY_MS_DEFAULT
    return value


def _recover_stale_submitting(qdb: LiveIntentQueueSQLite, ldb: LiveTradingSQLite, dedupe: OrderDedupeStore) -> dict:
    """
    Startup recovery for intents stranded at `submitting` by a crash between
    the dedupe claim/venue submit and the queue status write (fault-injection
    finding, substrate backlog #4).

    Fail-closed contract: this sweep NEVER submits. For each `submitting`
    intent older than the threshold, the venue is consulted by
    client_order_id:
      - order found  -> dedupe mark_submitted + status `submitted` (the
        normal reconciler lanes take over);
      - order absent -> status `submit_unknown` with a recovery reason (the
        reconciler's single ambiguity lane owns it);
      - lookup error -> the row is left untouched for the next restart.
    Rows younger than the threshold are left for the in-flight consumer.
    Missing/unparseable timestamps are treated as aged (the sweep itself is
    read-then-classify and cannot double-submit).
    """
    stale_ms = _submitting_stale_recovery_ms()
    now_epoch = datetime.now(timezone.utc).timestamp()
    out = {"scanned": 0, "recovered_submitted": 0, "moved_submit_unknown": 0, "left_untouched": 0}
    try:
        rows = qdb.list_intents(limit=200, status="submitting")
    except Exception as exc:
        _LOG.error("stale_submitting_recovery.list_failed err=%s:%s", type(exc).__name__, exc)
        return out
    aged = []
    for it in rows:
        out["scanned"] += 1
        ts_epoch = _parse_intent_ts_epoch(it.get("updated_ts") or it.get("created_ts"))
        if ts_epoch is not None and (now_epoch - ts_epoch) * 1000.0 < stale_ms:
            out["left_untouched"] += 1
            continue
        aged.append(it)
    if not aged:
        return out
    sandbox = _live_sandbox_enabled()
    adapters: dict[str, LiveExchangeAdapter] = {}
    try:
        for it in aged:
            ctx = LiveStateContext(authority="INTENT_CONSUMER", origin="live_intent_consumer.stale_submitting_recovery")
            venue = normalize_venue(it["venue"])
            symbol = normalize_symbol(it["symbol"])
            client_order_id = str(it.get("client_order_id") or f"live_intent_{it['intent_id']}")
            try:
                ad = adapters.get(venue)
                if ad is None:
                    ad = LiveExchangeAdapter(venue, sandbox=sandbox)
                    adapters[venue] = ad
                found = ad.find_order_by_client_oid(symbol, client_order_id)
            except Exception as exc:
                _LOG.warning(
                    "stale_submitting_recovery.lookup_failed intent_id=%s err=%s:%s — leaving untouched",
                    it.get("intent_id"), type(exc).__name__, exc,
                )
                out["left_untouched"] += 1
                continue
            ex_oid = str((found or {}).get("id") or (found or {}).get("orderId") or "").strip()
            if found and ex_oid:
                # a crash may have struck before dedupe.claim ever ran; claim is
                # an idempotent get-or-create, so the mark always has a row
                dedupe.claim(
                    exchange_id=venue,
                    intent_id=str(it["intent_id"]),
                    symbol=symbol,
                    client_order_id=client_order_id,
                    meta={"source": "live_intent_consumer.stale_submitting_recovery"},
                )
                dedupe.mark_submitted(exchange_id=venue, intent_id=str(it["intent_id"]), remote_order_id=ex_oid)
                if update_live_queue_status_as_intent_consumer(
                    qdb, it, "submitted", ctx=ctx, last_error=None,
                    client_order_id=client_order_id, exchange_order_id=ex_oid,
                ):
                    ldb.upsert_order({
                        "client_order_id": client_order_id,
                        "venue": venue, "symbol": symbol, "side": it["side"], "order_type": it["order_type"],
                        "qty": float(it["qty"]), "limit_price": it.get("limit_price"),
                        "exchange_order_id": ex_oid, "status": "submitted", "last_error": None,
                    })
                    out["recovered_submitted"] += 1
                else:
                    out["left_untouched"] += 1
                continue
            reason = "stale_submitting_recovery:order_not_found"
            if update_live_queue_status_as_intent_consumer(
                qdb, it, "submit_unknown", ctx=ctx, last_error=reason, client_order_id=client_order_id,
            ):
                ldb.upsert_order({
                    "client_order_id": client_order_id,
                    "venue": venue, "symbol": symbol, "side": it["side"], "order_type": it["order_type"],
                    "qty": float(it["qty"]), "limit_price": it.get("limit_price"),
                    "exchange_order_id": None, "status": "submit_unknown", "last_error": reason,
                })
                out["moved_submit_unknown"] += 1
            else:
                out["left_untouched"] += 1
    finally:
        for ad in adapters.values():
            try:
                ad.close()
            except Exception:
                pass
    return out


def _parse_intent_ts_epoch(raw) -> float | None:
    """Tolerant ISO/epoch parse mirroring intent_ttl semantics; None on failure."""
    from services.execution.intent_ttl import _parse_created_epoch

    return _parse_created_epoch(raw)


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
    dedupe = OrderDedupeStore()
    loops = 0
    submitted = 0
    rejected = 0
    expired = 0
    _write_status({"ok": True, "status": "running", "pid": os.getpid(), "ts": _now()})
    recovery = _recover_stale_submitting(qdb, ldb, dedupe)
    if recovery.get("scanned"):
        _write_status({"ok": True, "status": "running", "pid": os.getpid(), "ts": _now(), "note": "stale_submitting_recovery", **recovery})
    try:
        while True:
            loops += 1
            write_named_heartbeat("intent_consumer", extra={"loops": loops})
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
                _write_status({"ok": True, "status": "running", "ts": _now(), "loops": loops, "queue": 0, "submitted": submitted, "rejected": rejected, "expired": expired})
                time.sleep(0.6)
                continue
            sandbox = _live_sandbox_enabled()
            for it in batch:
                ctx = LiveStateContext(authority="INTENT_CONSUMER", origin="live_intent_consumer")
                ttl = check_intent_age(it.get("created_ts"))
                if not bool(ttl.get("ok")):
                    ttl_reason = str(ttl.get("reason") or "intent_ttl:unknown")
                    wrote = update_live_queue_status_as_intent_consumer(qdb, it, "expired", ctx=ctx, last_error=ttl_reason)
                    if wrote:
                        expired += 1
                        _write_status({"ok": True, "status": "running", "ts": _now(), "note": "intent_expired", "reason": ttl_reason, "intent": it.get("intent_id"), "expired": expired})
                    else:
                        _LOG.error("live_intent_consumer.intent_ttl_expiry_write_failed intent_id=%s reason=%s", it.get("intent_id"), ttl_reason)
                    continue
                venue = normalize_venue(it["venue"])
                symbol = normalize_symbol(it["symbol"])
                mq = mq_check(venue, symbol)
                if not mq.get("ok"):
                    mq_reason = f"mq_blocked:{mq.get('reason', 'unknown')}"
                    _write_status({"ok": True, "status": "running", "ts": _now(), "note": "market_quality_blocked", "blocked": mq, "intent": it.get("intent_id")})
                    wrote = update_live_queue_status_as_intent_consumer(qdb, it, "rejected", ctx=ctx, last_error=mq_reason)
                    if wrote:
                        rejected += 1
                    else:
                        _LOG.error("live_intent_consumer.mq_rejection_write_failed intent_id=%s reason=%s", it.get("intent_id"), mq_reason)
                        escalated = update_live_queue_status_as_intent_consumer(
                            qdb, it, "submit_unknown", ctx=ctx,
                            last_error=f"mq_rejected_write_failed:{mq_reason}",
                        )
                        if not escalated:
                            _LOG.error("live_intent_consumer.mq_submit_unknown_write_failed intent_id=%s reason=%s", it.get("intent_id"), mq_reason)
                    continue
                clock = check_venue_clock(venue, lambda v=venue: LiveExchangeAdapter(v, sandbox=sandbox))
                if not clock.get("ok"):
                    clock_reason = f"clock_skew_blocked:{clock.get('reason', 'unknown')}"
                    _write_status({"ok": True, "status": "running", "ts": _now(), "note": "clock_skew_blocked", "blocked": {k: clock.get(k) for k in ("venue", "skew_ms", "rtt_ms", "threshold_ms", "reason")}, "intent": it.get("intent_id")})
                    wrote = update_live_queue_status_as_intent_consumer(qdb, it, "rejected", ctx=ctx, last_error=clock_reason)
                    if wrote:
                        rejected += 1
                    else:
                        _LOG.error("live_intent_consumer.clock_rejection_write_failed intent_id=%s reason=%s", it.get("intent_id"), clock_reason)
                        escalated = update_live_queue_status_as_intent_consumer(
                            qdb, it, "submit_unknown", ctx=ctx,
                            last_error=f"clock_rejected_write_failed:{clock_reason}",
                        )
                        if not escalated:
                            _LOG.error("live_intent_consumer.clock_submit_unknown_write_failed intent_id=%s reason=%s", it.get("intent_id"), clock_reason)
                    continue
                notional_est = float(it["qty"]) * float(it.get("limit_price") or (mq.get("last") or 0.0) or 0.0)
                ok, rreason = _risk_check_and_claim(qdb, notional_est)
                if not ok:
                    wrote = update_live_queue_status_as_intent_consumer(qdb, it, "rejected", ctx=ctx, last_error=rreason)
                    if wrote:
                        rejected += 1
                    else:
                        _LOG.error("live_intent_consumer.risk_rejection_write_failed intent_id=%s reason=%s", it.get("intent_id"), rreason)
                        escalated = update_live_queue_status_as_intent_consumer(
                            qdb, it, "submit_unknown", ctx=ctx,
                            last_error=f"risk_rejected_write_failed:{rreason}",
                        )
                        if not escalated:
                            _LOG.error("live_intent_consumer.risk_submit_unknown_write_failed intent_id=%s reason=%s", it.get("intent_id"), rreason)
                    continue
                client_order_id = it.get("client_order_id") or f"live_intent_{it['intent_id']}"
                dedupe_row = dedupe.claim(
                    exchange_id=venue,
                    intent_id=str(it["intent_id"]),
                    symbol=symbol,
                    client_order_id=client_order_id,
                    meta={"source": "live_intent_consumer"},
                )
                dedupe_status = str(dedupe_row.get("status") or "").strip().lower()
                dedupe_remote_id = str(dedupe_row.get("remote_order_id") or "").strip()
                if dedupe_remote_id and dedupe_status in {"submitted", "acked", "terminal"}:
                    continue
                if (not bool(dedupe_row.get("_inserted"))) and dedupe_status in {"created", "submitted", "unknown"}:
                    continue

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
                        dedupe.mark_unknown(
                            exchange_id=venue,
                            intent_id=str(it["intent_id"]),
                            error="submit_response_missing_exchange_order_id",
                        )
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

                    dedupe.mark_submitted(
                        exchange_id=venue,
                        intent_id=str(it["intent_id"]),
                        remote_order_id=ex_oid,
                    )
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
                        dedupe.mark_submitted(
                            exchange_id=venue,
                            intent_id=str(it["intent_id"]),
                            remote_order_id=ex_oid,
                        )
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
            _write_status({"ok": True, "status": "running", "ts": _now(), "loops": loops, "submitted": submitted, "rejected": rejected, "expired": expired})
            time.sleep(0.4)
    finally:
        _release_lock()
        _write_status({"ok": True, "status": "stopped", "pid": os.getpid(), "ts": _now(), "loops": loops, "submitted": submitted, "rejected": rejected, "expired": expired})
