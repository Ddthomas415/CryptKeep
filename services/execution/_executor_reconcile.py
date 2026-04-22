from __future__ import annotations
from services.logging.app_logger import get_logger
_LOG = get_logger("_executor_reconcile")
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
from services.risk.live_risk_gates import (
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
    _client_id_from_reason,
    _record_execution_metric,
    _measure_ms,
    _load_execution_safety_cfg,
    _latency_tracker,
    LiveCfg,
    _is_live_shadow,
    _hard_off_guard,
    _list_intents_any,
    _open_reconcile_session,
    _close_reconcile_session,
    _fetch_order_for_reconcile,
    _fetch_trades_for_reconcile,
    _fetch_open_orders_for_reconcile,
)

def _trade_id(t: Dict[str, Any]) -> str:
    for k in ("id", "tradeId", "trade_id", "fillId", "fill_id"):
        v = t.get(k)
        if v:
            return str(v).strip()
    info = t.get("info")
    if isinstance(info, dict):
        for k in ("trade_id", "tradeId", "fill_id", "fillId", "id"):
            v = info.get(k)
            if v:
                return str(v).strip()
    return ""


def _trade_order_id(t: Dict[str, Any]) -> str:
    for k in ("order", "orderId", "order_id"):
        v = t.get(k)
        if v:
            return str(v).strip()
    info = t.get("info")
    if isinstance(info, dict):
        for k in ("order_id", "orderId", "order", "order_id_str"):
            v = info.get(k)
            if v:
                return str(v).strip()
    return ""


def _trade_client_id(t: Dict[str, Any]) -> str:
    for k in ("clientOrderId", "client_order_id", "clientId", "client_id", "text"):
        v = t.get(k)
        if v:
            return str(v).strip()
    info = t.get("info")
    if isinstance(info, dict):
        for k in ("clientOrderId", "client_order_id", "client_id", "clientId", "text"):
            v = info.get(k)
            if v:
                return str(v).strip()
    return ""


def _trade_ts_ms(t: Dict[str, Any]) -> int:
    raw = t.get("timestamp")
    if raw is None:
        return _now_ms()
    try:
        return int(float(raw))
    except Exception:
        return _now_ms()


def _trade_fee_parts(t: Dict[str, Any]) -> tuple[float, str]:
    fee_obj = t.get("fee")
    if isinstance(fee_obj, dict):
        fee_cost = float(fee_obj.get("cost") or 0.0)
        fee_ccy = str(fee_obj.get("currency") or "USD").upper()
        return fee_cost, (fee_ccy or "USD")
    return 0.0, "USD"


def _trade_matches_intent(trade: Dict[str, Any], *, remote_id: str | None, client_id: str | None) -> bool:
    remote = str(remote_id or "").strip()
    client = str(client_id or "").strip()
    trade_remote = _trade_order_id(trade)
    if remote and trade_remote and trade_remote == remote:
        return True
    trade_client = _trade_client_id(trade)
    if client and trade_client and trade_client == client:
        return True
    return False


def _existing_trade_ids(store: Any, *, intent_id: str) -> set[str]:
    getter = getattr(store, "list_fill_trade_ids", None)
    if callable(getter):
        try:
            rows = getter(intent_id=intent_id, limit=2000)
            return {str(v).strip() for v in rows if str(v or "").strip()}
        except Exception:
            return set()
    return set()


def reconcile_live(cfg: LiveCfg) -> Dict[str, Any]:
    ok, why = _hard_off_guard(cfg, operation="reconcile")
    if not ok:
        return {"ok": False, "note": why, "fills_added": 0}

    safety_cfg = _load_execution_safety_cfg()
    latency_tracker = _latency_tracker(safety_cfg)

    store = ExecutionStore(path=cfg.exec_db)
    store_dedupe = OrderDedupeStore(exec_db=cfg.exec_db)
    client = ExchangeClient(exchange_id=cfg.exchange_id, sandbox=cfg.sandbox)

    # track intents that are "submitted" (and sometimes pending with remote_id in reason)
    intents = _list_intents_any(store, mode="live", exchange=cfg.exchange_id, symbol=cfg.symbol, statuses=["submitted", "pending"], limit=200)

    fills_added = 0
    trade_fills_added = 0
    latency_fills_recorded = 0
    checked = 0
    session: Any | None = None
    session_owned = False
    try:
        for it in intents:
            if checked >= int(cfg.reconcile_limit):
                break
            checked += 1

            intent_id = str(it["intent_id"])
            reason = str(it.get("reason") or "")
            remote_id = _remote_id_from_reason(reason)
            if not remote_id:
                row_d = store_dedupe.get_by_intent(cfg.exchange_id, intent_id)
                remote_id = (row_d or {}).get("remote_order_id")
            if not remote_id:
                continue

            row_d = store_dedupe.get_by_intent(cfg.exchange_id, intent_id)
            cid = str((row_d or {}).get("client_order_id") or "").strip() or _client_id_from_reason(reason)
            known_trade_ids = _existing_trade_ids(store, intent_id=intent_id)

            if session is None:
                session, session_owned = _open_reconcile_session(client)
            fetch_order_started = time.perf_counter()
            try:
                o = _fetch_order_for_reconcile(
                    client,
                    session,
                    owned=session_owned,
                    venue=cfg.exchange_id,
                    symbol=str(it["symbol"]),
                    order_id=remote_id,
                )
            except Exception:
                _record_execution_metric(
                    name="reconcile_fetch_order_ms",
                    value_ms=_measure_ms(fetch_order_started),
                    meta={"exchange": cfg.exchange_id, "symbol": str(it["symbol"]), "intent_id": intent_id, "ok": False},
                    tracker=latency_tracker,
                )
                # keep tracking; don't spam submits
                continue
            _record_execution_metric(
                name="reconcile_fetch_order_ms",
                value_ms=_measure_ms(fetch_order_started),
                meta={"exchange": cfg.exchange_id, "symbol": str(it["symbol"]), "intent_id": intent_id, "ok": True},
                tracker=latency_tracker,
            )

            status = str(o.get("status") or "").lower()
            filled = float(o.get("filled") or 0.0)
            total_qty = float(it.get("qty") or 0.0)
            if status in ("open", "partially_filled"):
                if filled > 0.0 and filled < total_qty:
                    store.set_intent_status(
                        intent_id=intent_id,
                        status="partially_filled",
                        reason=f"remote_id={remote_id} filled={filled}/{total_qty}",
                    )
                    _LOG.info(
                        "reconcile partial fill intent=%s filled=%.6f/%.6f",
                        intent_id, filled, total_qty,
                    )
            avg = float(o.get("average") or (o.get("price") or 0.0) or 0.0)
            fee = o.get("fee") or {}
            fee_cost = float(fee.get("cost") or 0.0)
            fee_ccy = str(fee.get("currency") or "").upper() or "USD"

            trade_filled_qty = 0.0
            if bool(cfg.reconcile_trades):
                trades: list[dict[str, Any]] = []
                since_ms = max(0, _now_ms() - int(max(0, cfg.reconcile_lookback_ms)))
                fetch_trades = getattr(client, "fetch_my_trades", None)
                if session_owned or callable(fetch_trades):
                    if session is None:
                        session, session_owned = _open_reconcile_session(client)
                    fetch_trades_started = time.perf_counter()
                    try:
                        got = _fetch_trades_for_reconcile(
                            client,
                            session,
                            owned=session_owned,
                            venue=cfg.exchange_id,
                            symbol=str(it["symbol"]),
                            since_ms=since_ms,
                            limit=int(max(1, cfg.reconcile_trades_limit)),
                        )
                        if isinstance(got, list):
                            trades = [dict(x or {}) for x in got]
                    except Exception:
                        trades = []
                    _record_execution_metric(
                        name="reconcile_fetch_trades_ms",
                        value_ms=_measure_ms(fetch_trades_started),
                        meta={
                            "exchange": cfg.exchange_id,
                            "symbol": str(it["symbol"]),
                            "intent_id": intent_id,
                            "trade_count": len(trades),
                        },
                        tracker=latency_tracker,
                    )

                for tr in trades:
                    if not _trade_matches_intent(tr, remote_id=remote_id, client_id=cid):
                        continue
                    qty = float(tr.get("amount") or tr.get("qty") or 0.0)
                    px = float(tr.get("price") or 0.0)
                    if qty <= 0.0 or px <= 0.0:
                        continue
                    trade_filled_qty += qty
                    trade_id = _trade_id(tr)
                    if not trade_id or trade_id in known_trade_ids:
                        continue
                    t_fee_cost, t_fee_ccy = _trade_fee_parts(tr)
                    t_ts_ms = _trade_ts_ms(tr)
                    store.add_fill(
                        intent_id=intent_id,
                        ts_ms=t_ts_ms,
                        price=px,
                        qty=qty,
                        fee=t_fee_cost,
                        fee_ccy=t_fee_ccy,
                        meta={
                            "remote_order_id": remote_id,
                            "status": status,
                            "trade_id": trade_id,
                            "raw_trade": {
                                "id": tr.get("id"),
                                "order": tr.get("order"),
                                "timestamp": tr.get("timestamp"),
                                "price": tr.get("price"),
                                "amount": tr.get("amount"),
                                "fee": tr.get("fee"),
                            },
                        },
                    )
                    known_trade_ids.add(trade_id)
                    fills_added += 1
                    trade_fills_added += 1
                    if cid:
                        try:
                            latency_tracker.record_fill(
                                client_order_id=cid,
                                exchange=cfg.exchange_id,
                                symbol=str(it["symbol"]),
                                price=px,
                                qty=qty,
                            )
                            latency_fills_recorded += 1
                        except Exception as _silent_err:
                            _LOG.debug("suppressed: %s", _silent_err)

            # Trade-level reconciliation handles partial fills + fees.
            # Keep synthetic fallback when closed fills are available but per-trade rows are not.
            if status in ("closed", "filled") and filled > 0 and avg > 0:
                if trade_filled_qty <= 0.0:
                    store.add_fill(
                        intent_id=intent_id,
                        ts_ms=_now_ms(),
                        price=avg,
                        qty=filled,
                        fee=fee_cost,
                        fee_ccy=fee_ccy,
                        meta={"remote_order_id": remote_id, "status": status, "raw_order": {"id": o.get("id"), "filled": filled, "average": avg, "fee": fee}},
                    )
                    fills_added += 1
                    if cid:
                        try:
                            latency_tracker.record_fill(
                                client_order_id=cid,
                                exchange=cfg.exchange_id,
                                symbol=str(it["symbol"]),
                                price=avg,
                                qty=filled,
                            )
                            latency_fills_recorded += 1
                        except Exception as _silent_err:
                            _LOG.debug("suppressed: %s", _silent_err)
                store.set_intent_status(intent_id=intent_id, status="filled", reason=f"remote_id={remote_id}")

                try:
                    store_dedupe.mark_terminal(exchange_id=cfg.exchange_id, intent_id=intent_id, terminal_status=status)
                except Exception as _silent_err:
                    _LOG.debug("suppressed: %s", _silent_err)
            elif status in ("canceled", "cancelled", "rejected", "expired"):
                store.set_intent_status(intent_id=intent_id, status="canceled", reason=f"remote_id={remote_id}:{status}")
                try:
                    store_dedupe.mark_terminal(exchange_id=cfg.exchange_id, intent_id=intent_id, terminal_status=status)
                except Exception as _silent_err:
                    _LOG.debug("suppressed: %s", _silent_err)
    finally:
        _close_reconcile_session(session, owned=session_owned)

    return {
        "ok": True,
        "note": "reconcile complete",
        "checked": checked,
        "fills_added": fills_added,
        "trade_fills_added": trade_fills_added,
        "latency_fills_recorded": latency_fills_recorded,
        "observe_only": _is_live_shadow(cfg),
    }
# PHASE82_LIVE_GATES


# ---------------- PHASE 85: open-orders reconcile helpers ----------------
def _extract_client_id(o: dict) -> str:
    for k in ("clientOrderId", "client_order_id", "text"):
        v = o.get(k)
        if v:
            return str(v)
    info = o.get("info")
    if isinstance(info, dict):
        for k in ("clientOrderId", "client_order_id", "text", "client_id"):
            v = info.get(k)
            if v:
                return str(v)
    return ""

def reconcile_open_orders(exec_db: str, exchange_id: str, *, limit: int = 200, sandbox: bool = False) -> dict:
    ex_id = (exchange_id or "").lower().strip()
    store = OrderDedupeStore(exec_db=exec_db)
    client = ExchangeClient(exchange_id=ex_id, sandbox=bool(sandbox))
    session, session_owned = _open_reconcile_session(client)
    rows = store.list_needs_reconcile(exchange_id=ex_id, limit=int(limit))
    by_sym = {}
    try:
        for r in rows:
            sym = str(r.get("symbol") or "")
            if sym:
                by_sym.setdefault(sym, []).append(r)
        matched = 0
        for sym, rs in by_sym.items():
            want = {str(r.get("client_order_id") or ""): str(r.get("intent_id") or "") for r in rs}
            want = {k:v for k,v in want.items() if k}
            if not want:
                continue
            try:
                fetch_open_orders_started = time.perf_counter()
                oo = _fetch_open_orders_for_reconcile(
                    client,
                    session,
                    owned=session_owned,
                    venue=ex_id,
                    symbol=sym,
                )
            except Exception:
                oo = []
                _record_execution_metric(
                    name="reconcile_open_orders_fetch_ms",
                    value_ms=_measure_ms(fetch_open_orders_started),
                    meta={"exchange": ex_id, "symbol": sym, "ok": False},
                    tracker=client,
                    latency_db_path=str(data_dir() / "market_ws.sqlite"),
                )
            else:
                _record_execution_metric(
                    name="reconcile_open_orders_fetch_ms",
                    value_ms=_measure_ms(fetch_open_orders_started),
                    meta={"exchange": ex_id, "symbol": sym, "ok": True, "open_orders": len(oo)},
                    tracker=client,
                    latency_db_path=str(data_dir() / "market_ws.sqlite"),
                )
            for o in oo:
                cid = _extract_client_id(o)
                if cid and cid in want:
                    intent_id = want[cid]
                    rid = o.get("id")
                    if rid:
                        store.set_remote_id_if_empty(exchange_id=ex_id, intent_id=intent_id, remote_order_id=str(rid))
                        store.mark_submitted(exchange_id=ex_id, intent_id=intent_id, remote_order_id=str(rid))
                        matched += 1
    finally:
        _close_reconcile_session(session, owned=session_owned)
    return {"ok": True, "rows": len(rows), "matched_open": matched}

def _env_symbol(default: str = "BTC/USD") -> str:
    s = (os.environ.get("CBP_SYMBOLS") or "").split(",")[0].strip()
    if not s:
        raise RuntimeError("CBP_CONFIG_REQUIRED:missing_env:CBP_SYMBOLS")
    return s

def _env_venue(default: str = "coinbase") -> str:
    v = (os.environ.get("CBP_VENUE") or "").strip().lower()
    if not v:
        raise RuntimeError("CBP_CONFIG_REQUIRED:missing_env:CBP_VENUE")
    return v
