from __future__ import annotations
from services.logging.app_logger import get_logger
_LOG = get_logger("_executor_submit")
from services.risk.market_quality_guard import check_market_quality

import os
import logging
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from services.config_loader import load_runtime_trading_config
from services.admin.system_guard import get_state as get_system_guard_state
from services.execution.live_arming import live_armed_signal
from services.execution.client_order_id import make_client_order_id
from services.execution.execution_latency import ExecutionLatencyTracker
from services.execution.lifecycle_boundary import (
    fetch_open_orders_via_boundary,
    fetch_my_trades_via_boundary,
    fetch_order_via_boundary,
)
from services.execution.safety_gates import SafetyConfig
from services.execution.exchange_client import ExchangeClient
from services.journal.fill_sink import CanonicalFillSink
from services.market_data.tick_reader import get_best_bid_ask_last
from services.os.app_paths import data_dir, ensure_dirs
from services.preflight.preflight import run_preflight
from services.risk.live_risk_gates_phase82 import (
    LiveRiskLimits,
    LiveGateDB,
    LiveRiskGates,
    phase83_incr_trade_counter,
)  # PHASE82_LIVE_GATES
from services.risk.risk_daily import RiskDailyDB
from services.risk.staleness_guard import is_snapshot_fresh
from storage.execution_store_sqlite import ExecutionStore
from storage.market_ws_store_sqlite import SQLiteMarketWsStore
from storage.order_dedupe_store_sqlite import OrderDedupeStore
from storage.ws_status_sqlite import WSStatusSQLite

_LOG = logging.getLogger(__name__)

# Module-level cache for config that does not change tick-to-tick.
# Keyed by file path, value is (mtime_float, parsed_config).
_yaml_cache: dict[str, tuple[float, dict]] = {}
_yaml_cache_lock = threading.Lock()

from services.execution._executor_shared import (
    _now_ms,
    _remote_id_from_reason,
    _load_execution_safety_cfg,
    _latency_tracker,
    _check_market_freshness_for_live,
    _execution_safety_pause_open,
    _check_preflight_gate,
    LiveCfg,
    _hard_off_guard,
    _system_guard_submit_open,
    _list_intents_any,
    _local_gate_price,
)

def submit_pending_live(cfg: LiveCfg) -> Dict[str, Any]:
    ok, why = _hard_off_guard(cfg, operation="submit")
    if not ok:
        if str(why).startswith("LIVE_SHADOW"):
            return {"ok": True, "note": why, "submitted": 0, "errors": 0, "observe_only": True}
        return {"ok": False, "note": why, "submitted": 0}

    guard_ok, guard_reason, guard_meta = _system_guard_submit_open()
    if not guard_ok:
        return {
            "ok": False,
            "note": f"LIVE blocked: {guard_reason}",
            "submitted": 0,
            "errors": 0,
            "preflight_blocked": 0,
            "safety_blocked": 1,
            "latency_breaches": 0,
            "system_guard": guard_meta,
        }

    safety_cfg = _load_execution_safety_cfg()
    safety_ok, safety_reason, safety_meta = _execution_safety_pause_open()
    if not safety_ok:
        return {
            "ok": False,
            "note": f"LIVE blocked: {safety_reason}",
            "submitted": 0,
            "errors": 0,
            "preflight_blocked": 0,
            "safety_blocked": 1,
            "latency_breaches": 0,
            "safety": safety_meta,
        }

    fresh_ok, fresh_reason, fresh_meta = _check_market_freshness_for_live(cfg, safety_cfg)
    if not fresh_ok:
        return {
            "ok": False,
            "note": f"LIVE blocked: {fresh_reason}",
            "submitted": 0,
            "errors": 0,
            "preflight_blocked": 0,
            "safety_blocked": 1,
            "latency_breaches": 0,
            "safety": fresh_meta,
        }

    latency_tracker = _latency_tracker(safety_cfg)

    # PHASE82_LIVE_GATES init
    _cfg_cached = load_runtime_trading_config()
    limits = LiveRiskLimits.from_dict(_cfg_cached)
    gate_db = LiveGateDB(exec_db=cfg.exec_db)
    gates = LiveRiskGates(limits=limits, db=gate_db) if limits else None
    if not gates:
        return {'ok': False, 'note': 'LIVE blocked: risk limits missing/invalid', 'submitted': 0}
    if gate_db.killswitch_on():
        return {'ok': False, 'note': 'LIVE blocked: kill switch ON', 'submitted': 0}

    store = ExecutionStore(path=cfg.exec_db)
    store_dedupe = OrderDedupeStore(exec_db=cfg.exec_db)
    client = ExchangeClient(exchange_id=cfg.exchange_id, sandbox=cfg.sandbox)

    pending = _list_intents_any(store, mode="live", exchange=cfg.exchange_id, symbol=cfg.symbol, statuses=["pending"], limit=200)
    submitted = 0
    errors = 0
    preflight_blocked = 0
    safety_blocked = 0
    latency_breaches = 0

    for it in pending:
        if submitted >= int(cfg.max_submit_per_tick):
            break

        intent_id = str(it["intent_id"])
        try:
            mq_ok, mq_reason = check_market_quality(cfg.exchange_id, str(it.get("symbol") or ""))
        except Exception as exc:
            _LOG.warning("market_quality_guard error symbol=%s: %s", it.get("symbol"), exc)
            mq_ok, mq_reason = True, "guard_error_passthrough"

        if not mq_ok:
            store.set_intent_status(
                intent_id=intent_id,
                status="pending",
                reason=f"market_quality_block:{mq_reason}",
            )
            _LOG.info("market_quality_gate blocked intent=%s reason=%s", intent_id, mq_reason)
            continue

        _get_symbol_lock = getattr(store, "get_symbol_lock", None)
        _sym_lock = _get_symbol_lock(str(it.get("symbol") or "")) if callable(_get_symbol_lock) else None
        if _sym_lock is not None:
            _lock_remaining_sec = max(0, (_sym_lock["locked_until_ms"] - _now_ms()) // 1000)
            store.set_intent_status(
                intent_id=intent_id,
                status="pending",
                reason=f"symbol_locked:{_sym_lock['reason']} remaining={_lock_remaining_sec}s",
            )
            _LOG.info(
                "symbol_lock blocked intent=%s symbol=%s remaining=%ss",
                intent_id, it.get("symbol"), _lock_remaining_sec,
            )
            continue

        meta = dict(it.get("meta") or {})
        reason0 = str(it.get("reason") or "")
        rid0 = _remote_id_from_reason(reason0)
        if rid0:
            store.set_intent_status(intent_id=intent_id, status="submitted", reason=f"remote_id={rid0}")
            continue
        cid = make_client_order_id(cfg.exchange_id, intent_id)
        try:
            # PHASE82_LIVE_GATES enforce
            rpnl = float(RiskDailyDB(cfg.exec_db).realized_today_usd())
            lp = (float(it['limit_price']) if it.get('limit_price') is not None else None)
            if lp is None:
                side0 = str(it.get('side') or '').lower()
                lp = _local_gate_price(cfg, side=side0)
                if lp is None:
                    store.set_intent_status(
                        intent_id=intent_id,
                        status="pending",
                        reason="live_gate_block:missing_local_quote",
                    )
                    continue
            ok2, reason2, meta2 = gates.check_live(it={'qty': float(it.get('qty') or 0.0), 'price': lp, 'symbol': str(it.get('symbol') or '')}, realized_pnl_usd=rpnl)
            if not ok2:
                store.set_intent_status(intent_id=intent_id, status='pending', reason=f'live_gate_block:{reason2}')
                continue

            pf_ok, pf_reason, pf_meta = _check_preflight_gate(cfg)
            if not pf_ok:
                preflight_blocked += 1
                detail = str(pf_meta.get("error") or pf_reason)
                store.set_intent_status(intent_id=intent_id, status="pending", reason=f"preflight_gate_block:{pf_reason}:{detail}")
                # Pause state applies to all live submits this tick.
                if pf_reason in {"CIRCUIT_BREAKER_TRIPPED", "CIRCUIT_BREAKER_PAUSED"}:
                    break
                continue

            submit_started = _now_ms()
            latency_tracker.record_submit(
                client_order_id=cid,
                exchange=cfg.exchange_id,
                symbol=str(it["symbol"]),
                side=str(it["side"]),
                qty=float(it["qty"]),
            )
            order = client.submit_order(
                symbol=str(it["symbol"]),
                side=str(it["side"]),
                order_type=str(it["order_type"]),
                amount=float(it["qty"]),
                price=(float(it["limit_price"]) if it.get("limit_price") is not None else None),
                client_id=cid,
                extra_params=None,
                intent_id=intent_id,
                exec_db=cfg.exec_db,
            )
            latency_tracker.record_ack(
                client_order_id=cid,
                exchange=cfg.exchange_id,
                symbol=str(it["symbol"]),
                exchange_order_id=(order.get("id") if isinstance(order, dict) else None),
            )
            meta["client_id"] = cid
            meta["remote_order_id"] = order.get("id")
            meta["sent_ts_ms"] = _now_ms()
            # store meta back: simplest is to re-submit a no-op? we don't have meta update method; encode into reason for now
            # We'll store remote id in reason field and keep full meta in fills later.
            row_d = store_dedupe.get_by_intent(cfg.exchange_id, intent_id)
            cid2 = (row_d or {}).get("client_order_id") or cid
            rid2 = (row_d or {}).get("remote_order_id") or order.get("id")
            store.set_intent_status(intent_id=intent_id, status="submitted", reason=f"remote_id={rid2} client_id={cid2}")

            # LIVE_SUBMIT_SUCCESS_ANCHOR
            try:
                phase83_incr_trade_counter(cfg.exec_db, gate_db=gate_db)
            except Exception as _silent_err:
                _LOG.debug("suppressed: %s", _silent_err)

            # EXEC_GUARD_TRADE_ATTEMPT
            try:
                from storage.execution_guard_store_sqlite import ExecutionGuardStoreSQLite
                ExecutionGuardStoreSQLite()._record_trade_attempt_sync()
            except Exception as _silent_err:
                _LOG.debug("suppressed: %s", _silent_err)
            submitted += 1

            ack_ms = max(0, _now_ms() - submit_started)
            if safety_cfg.enabled and ack_ms > int(safety_cfg.max_ack_ms):
                latency_breaches += 1
                _EXECUTION_SAFETY_CIRCUIT.pause_until_ts = time.time() + float(max(1, int(safety_cfg.pause_seconds_on_breach)))
                _EXECUTION_SAFETY_CIRCUIT.last_reason = f"submit_to_ack_ms:{ack_ms}"
                safety_blocked += 1
                # Submit already happened; stop submitting additional orders this tick.
                break
        except Exception as e:
            errors += 1
            store.set_intent_status(intent_id=intent_id, status="pending", reason=f"submit_error:{type(e).__name__}:{e}")

    return {
        "ok": True,
        "note": "submitted tick complete",
        "submitted": submitted,
        "errors": errors,
        "preflight_blocked": preflight_blocked,
        "safety_blocked": safety_blocked,
        "latency_breaches": latency_breaches,
    }

