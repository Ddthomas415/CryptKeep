"""services/execution/live_executor.py — public API facade."""
from __future__ import annotations

import services.execution._executor_reconcile as _reconcile
import services.execution._executor_shared as _shared
import services.execution._executor_submit as _submit

from services.execution._executor_reconcile import (  # noqa: F401
    _env_symbol,
    _env_venue,
    reconcile_live as _reconcile_live_impl,
    reconcile_open_orders as _reconcile_open_orders_impl,
)
from services.execution._executor_shared import (  # noqa: F401
    LiveCfg,
    _EXECUTION_SAFETY_CIRCUIT,
    _PreflightCircuitState,
    _check_market_freshness_for_live as _check_market_freshness_for_live_impl,
    _check_preflight_gate as _check_preflight_gate_impl,
    _execution_safety_pause_open as _execution_safety_pause_open_impl,
    _hard_off_guard as _hard_off_guard_impl,
    _latency_tracker as _latency_tracker_impl,
    _load_execution_safety_cfg as _load_execution_safety_cfg_impl,
    _now_ms as _now_ms_impl,
    cfg_from_yaml as _cfg_from_yaml_impl,
    check_market_quality,
    get_system_guard_state,
    live_armed_signal,
    load_runtime_trading_config,
    make_client_order_id,
    run_preflight,
)
from services.execution._executor_submit import submit_pending_live as _submit_pending_live_impl  # noqa: F401
from services.execution.exchange_client import ExchangeClient  # noqa: F401
from services.market_data.tick_reader import get_best_bid_ask_last  # noqa: F401
from services.risk.live_risk_gates import (  # noqa: F401
    LiveGateDB,
    LiveRiskGates,
    LiveRiskLimits,
    phase83_incr_trade_counter,
)
from services.risk.risk_daily import RiskDailyDB  # noqa: F401
from storage.execution_store_sqlite import ExecutionStore  # noqa: F401
from storage.market_ws_store_sqlite import SQLiteMarketWsStore  # noqa: F401
from storage.order_dedupe_store_sqlite import OrderDedupeStore  # noqa: F401

time = _submit.time  # noqa: F401

_SHARED_SYNC_ATTRS = (
    "SQLiteMarketWsStore",
    "check_market_quality",
    "get_best_bid_ask_last",
    "get_system_guard_state",
    "live_armed_signal",
    "load_runtime_trading_config",
    "run_preflight",
    "_check_market_freshness_for_live",
    "_check_preflight_gate",
    "_execution_safety_pause_open",
    "_latency_tracker",
    "_load_execution_safety_cfg",
    "_now_ms",
    "_hard_off_guard",
    "_EXECUTION_SAFETY_CIRCUIT",
)

_SUBMIT_SYNC_ATTRS = (
    "check_market_quality",
    "_check_market_freshness_for_live",
    "_check_preflight_gate",
    "_execution_safety_pause_open",
    "_EXECUTION_SAFETY_CIRCUIT",
    "_latency_tracker",
    "_load_execution_safety_cfg",
    "_now_ms",
    "ExecutionStore",
    "ExchangeClient",
    "LiveGateDB",
    "LiveRiskGates",
    "OrderDedupeStore",
    "RiskDailyDB",
    "get_best_bid_ask_last",
    "phase83_incr_trade_counter",
)

_RECONCILE_SYNC_ATTRS = (
    "check_market_quality",
    "_latency_tracker",
    "_load_execution_safety_cfg",
    "_now_ms",
    "ExecutionStore",
    "ExchangeClient",
    "OrderDedupeStore",
    "SQLiteMarketWsStore",
)


def _sync_live_executor_compat() -> None:
    for name in _SHARED_SYNC_ATTRS:
        setattr(_shared, name, globals()[name])
    for name in _SUBMIT_SYNC_ATTRS:
        setattr(_submit, name, globals()[name])
    for name in _RECONCILE_SYNC_ATTRS:
        setattr(_reconcile, name, globals()[name])


def cfg_from_yaml(path: str = "config/trading.yaml") -> LiveCfg:
    _sync_live_executor_compat()
    return _cfg_from_yaml_impl(path)


def _load_execution_safety_cfg(*args, **kwargs):
    _sync_live_executor_compat()
    return _load_execution_safety_cfg_impl(*args, **kwargs)


def _latency_tracker(*args, **kwargs):
    _sync_live_executor_compat()
    return _latency_tracker_impl(*args, **kwargs)


def _execution_safety_pause_open(*args, **kwargs):
    _sync_live_executor_compat()
    return _execution_safety_pause_open_impl(*args, **kwargs)


def _check_market_freshness_for_live(*args, **kwargs):
    _sync_live_executor_compat()
    return _check_market_freshness_for_live_impl(*args, **kwargs)


def _check_preflight_gate(*args, **kwargs):
    _sync_live_executor_compat()
    return _check_preflight_gate_impl(*args, **kwargs)


def _hard_off_guard(*args, **kwargs):
    _sync_live_executor_compat()
    return _hard_off_guard_impl(*args, **kwargs)


def _now_ms(*args, **kwargs):
    _sync_live_executor_compat()
    return _now_ms_impl(*args, **kwargs)


def _on_fill(fill, *, exec_db: str | None = None):
    _sync_live_executor_compat()
    return _shared._on_fill(fill, exec_db=exec_db)


def submit_pending_live(cfg: LiveCfg):
    _sync_live_executor_compat()
    return _submit_pending_live_impl(cfg)


def reconcile_live(cfg: LiveCfg):
    _sync_live_executor_compat()
    return _reconcile_live_impl(cfg)


def reconcile_open_orders(*args, **kwargs):
    _sync_live_executor_compat()
    return _reconcile_open_orders_impl(*args, **kwargs)
