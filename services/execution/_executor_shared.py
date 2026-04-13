from __future__ import annotations
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

def _load_yaml_cached(path: str) -> dict:
    """Load a YAML file with mtime-based cache (thread-safe)."""
    p = Path(path)
    try:
        mtime = p.stat().st_mtime
    except FileNotFoundError:
        return {}
    with _yaml_cache_lock:
        cached = _yaml_cache.get(path)
        if cached is not None and cached[0] == mtime:
            return cached[1]
    # Read outside the lock — file I/O should not block other threads
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except Exception:
        data = {}
    with _yaml_cache_lock:
        _yaml_cache[path] = (mtime, data)
    return data

# ---- runtime defaults (override by env set from scripts/bot_ctl.py) ----
DEFAULT_SYMBOL = ([x.strip() for x in (os.environ.get("CBP_SYMBOLS") or "").split(",") if x.strip()] or [""])[0]


def _default_exec_db_path() -> str:
    return str(
        os.environ.get("EXEC_DB_PATH")
        or os.environ.get("CBP_DB_PATH")
        or (data_dir() / "execution.sqlite")
    )


def _on_fill(fill: Dict[str, Any], *, exec_db: str | None = None) -> Dict[str, Any]:
    """
    Canonical fill choke point for live feeds.
    User-stream/REST fill adapters should call this helper so fills always flow
    through the same sink and idempotent journal path.
    """
    db_path = str(exec_db or _default_exec_db_path())
    try:
        CanonicalFillSink(exec_db=db_path).on_fill(dict(fill or {}))
        return {
            "ok": True,
            "exec_db": db_path,
            "venue": str((fill or {}).get("venue") or (fill or {}).get("exchange") or ""),
            "fill_id": str((fill or {}).get("fill_id") or (fill or {}).get("id") or ""),
        }
    except Exception as e:
        return {"ok": False, "exec_db": db_path, "error": f"{type(e).__name__}:{e}"}


def _now_ms() -> int:
    return int(time.time() * 1000)


def _remote_id_from_reason(reason: str) -> Optional[str]:
    s = (reason or "").strip()
    if "remote_id=" in s:
        return s.split("remote_id=", 1)[-1].split()[0].strip() or None
    return None


def _client_id_from_reason(reason: str) -> Optional[str]:
    s = (reason or "").strip()
    for token in ("client_id=", "client_order_id="):
        if token in s:
            return s.split(token, 1)[-1].split()[0].strip() or None
    return None


def _truthy(v: str | None, *, default: bool = False) -> bool:
    if v is None:
        return default
    return str(v).strip().lower() in {"1", "true", "yes", "on", "y"}


def _boolish(v: Any, *, default: bool = False) -> bool:
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    return str(v).strip().lower() in {"1", "true", "yes", "on", "y"}


def _first_preflight_error(checks: list[dict[str, Any]]) -> str:
    for item in checks:
        if not bool(item.get("ok", False)) and str(item.get("severity") or "").upper() == "ERROR":
            detail = str(item.get("detail") or "").strip()
            if detail:
                return detail
            name = str(item.get("name") or "").strip()
            if name:
                return name
    return "preflight_failed"


@dataclass
class _PreflightCircuitState:
    consecutive_failures: int = 0
    pause_until_ts: float = 0.0
    last_reason: str = ""


_PREFLIGHT_CIRCUIT = _PreflightCircuitState()


@dataclass
class _ExecutionSafetyCircuitState:
    pause_until_ts: float = 0.0
    last_reason: str = ""


_EXECUTION_SAFETY_CIRCUIT = _ExecutionSafetyCircuitState()


def _record_execution_metric(
    *,
    name: str,
    value_ms: float,
    meta: dict[str, Any] | None = None,
    tracker: Any | None = None,
    latency_db_path: str | None = None,
) -> None:
    payload = dict(meta or {})
    try:
        if tracker is not None:
            record_measurement = getattr(tracker, "record_measurement", None)
            if callable(record_measurement):
                record_measurement(name=name, value_ms=value_ms, meta=payload, category="execution")
                return
            store = getattr(tracker, "store", None)
            log_latency = getattr(store, "log_latency", None)
            if callable(log_latency):
                log_latency(
                    ts_ms=_now_ms(),
                    category="execution",
                    name=name,
                    value_ms=max(0.0, float(value_ms)),
                    meta=payload,
                )
                return
        db_path = str(latency_db_path or (data_dir() / "market_ws.sqlite"))
        SQLiteMarketWsStore(path=db_path).log_latency(
            ts_ms=_now_ms(),
            category="execution",
            name=name,
            value_ms=max(0.0, float(value_ms)),
            meta=payload,
        )
    except Exception:
        pass


def _measure_ms(start_ts: float) -> float:
    return max(0.0, (time.perf_counter() - float(start_ts)) * 1000.0)


def _load_execution_safety_cfg(cfg_path: str = "config/trading.yaml") -> SafetyConfig:
    started = time.perf_counter()
    latency_db_path = str(data_dir() / "market_ws.sqlite")
    cfg = load_runtime_trading_config(cfg_path)
    sec = cfg.get("execution_safety") or {}
    if not isinstance(sec, dict):
        sec = {}
    latency_db_path = str(sec.get("latency_db_path") or latency_db_path)
    out = SafetyConfig(
        enabled=bool(sec.get("enabled", True)),
        max_ws_recv_age_ms=int(sec.get("max_ws_recv_age_ms", 1500) or 1500),
        max_ack_ms=int(sec.get("max_ack_ms", 3000) or 3000),
        pause_seconds_on_breach=int(sec.get("pause_seconds_on_breach", 30) or 30),
        require_ws_fresh_for_live=bool(sec.get("require_ws_fresh_for_live", True)),
        latency_db_path=latency_db_path,
    )
    _record_execution_metric(
        name="execution_safety_cfg_load_ms",
        value_ms=_measure_ms(started),
        meta={"cfg_path": str(cfg_path)},
        latency_db_path=latency_db_path,
    )
    return out


def _latency_tracker(cfg: SafetyConfig) -> ExecutionLatencyTracker:
    return ExecutionLatencyTracker(store=SQLiteMarketWsStore(path=cfg.latency_db_path))


def _ws_status_store() -> WSStatusSQLite:
    return WSStatusSQLite()


def _check_market_freshness_for_live(
    cfg: "LiveCfg",
    safety_cfg: SafetyConfig,
    *,
    ws_db: WSStatusSQLite | None = None,
    now_ms: int | None = None,
) -> tuple[bool, str, dict[str, Any]]:
    if not safety_cfg.enabled or not safety_cfg.require_ws_fresh_for_live:
        return True, "WS_FRESHNESS_DISABLED", {"enforced": False}

    db = ws_db or _ws_status_store()
    now_v = int(now_ms) if now_ms is not None else _now_ms()
    row = db.get_status(exchange=cfg.exchange_id, symbol=cfg.symbol)
    if row:
        recv_ts_ms = int(row.get("recv_ts_ms") or 0)
        recv_age_ms = now_v - recv_ts_ms if recv_ts_ms else 10**9
        ok = recv_age_ms <= int(safety_cfg.max_ws_recv_age_ms)
        if ok:
            return True, "WS_FRESH_OK", {
                "source": "ws_status",
                "recv_ts_ms": recv_ts_ms,
                "recv_age_ms": recv_age_ms,
                "max_ws_recv_age_ms": int(safety_cfg.max_ws_recv_age_ms),
            }
        return False, "WS_STALE", {
            "source": "ws_status",
            "recv_ts_ms": recv_ts_ms,
            "recv_age_ms": recv_age_ms,
            "max_ws_recv_age_ms": int(safety_cfg.max_ws_recv_age_ms),
        }

    max_age_sec = max(0.1, float(safety_cfg.max_ws_recv_age_ms) / 1000.0)
    snap_ok, snap_reason = is_snapshot_fresh(max_age_sec=max_age_sec)
    if snap_ok:
        return True, "WS_FRESH_OK_SNAPSHOT", {"source": "snapshot", "max_age_sec": max_age_sec}
    return False, "WS_MISSING_OR_STALE", {"source": "snapshot", "reason": snap_reason, "max_age_sec": max_age_sec}


def _execution_safety_pause_open(
    *,
    state: _ExecutionSafetyCircuitState = _EXECUTION_SAFETY_CIRCUIT,
    now_ts: float | None = None,
) -> tuple[bool, str, dict[str, Any]]:
    now = float(now_ts) if now_ts is not None else time.time()
    if state.pause_until_ts > now:
        return False, "ACK_LATENCY_PAUSED", {
            "pause_until_ts": state.pause_until_ts,
            "pause_remaining_s": round(max(0.0, state.pause_until_ts - now), 3),
            "last_reason": state.last_reason,
        }
    return True, "OK", {}


def _check_preflight_gate(
    cfg: "LiveCfg",
    *,
    cfg_path: str = "config/trading.yaml",
    state: _PreflightCircuitState = _PREFLIGHT_CIRCUIT,
    now_ts: float | None = None,
) -> tuple[bool, str, dict[str, Any]]:
    enforce = _truthy(os.environ.get("CBP_LIVE_PREFLIGHT_ENFORCE"), default=True)
    if not enforce:
        return True, "PREFLIGHT_GATE_DISABLED", {"enforced": False}

    now = float(now_ts) if now_ts is not None else time.time()
    if state.pause_until_ts > now:
        return False, "CIRCUIT_BREAKER_PAUSED", {
            "pause_until_ts": state.pause_until_ts,
            "pause_remaining_s": round(max(0.0, state.pause_until_ts - now), 3),
            "last_reason": state.last_reason,
        }

    pf = run_preflight(cfg_path=cfg_path)
    checks = list(getattr(pf, "checks", []) or [])
    if bool(getattr(pf, "ok", False)):
        state.consecutive_failures = 0
        state.last_reason = ""
        return True, "OK", {"checks": checks}

    state.consecutive_failures += 1
    threshold = max(1, int(os.environ.get("CBP_LIVE_PREFLIGHT_FAIL_THRESHOLD") or 3))
    pause_s = max(1.0, float(os.environ.get("CBP_LIVE_PREFLIGHT_PAUSE_SECONDS") or 30.0))
    detail = _first_preflight_error(checks)
    state.last_reason = detail

    meta: dict[str, Any] = {
        "checks": checks,
        "error": detail,
        "consecutive_failures": state.consecutive_failures,
        "threshold": threshold,
    }

    if state.consecutive_failures >= threshold:
        state.pause_until_ts = now + pause_s
        state.consecutive_failures = 0
        meta["pause_seconds"] = pause_s
        meta["pause_until_ts"] = state.pause_until_ts
        return False, "CIRCUIT_BREAKER_TRIPPED", meta

    return False, "PREFLIGHT_FAILED", meta


@dataclass
class LiveCfg:
    enabled: bool = False
    observe_only: bool = False
    sandbox: bool = False
    exchange_id: str = ""
    exec_db: str = ""
    symbol: str = ""
    max_submit_per_tick: int = 1
    reconcile_limit: int = 25
    reconcile_trades: bool = True
    reconcile_lookback_ms: int = 6 * 60 * 60 * 1000
    reconcile_trades_limit: int = 200

def cfg_from_yaml(path: str = "config/trading.yaml") -> LiveCfg:
    ensure_dirs()
    started = time.perf_counter()
    cfg = load_runtime_trading_config(path)
    live = cfg.get("live") or {}
    ex_cfg = cfg.get("execution") or {}
    sec = cfg.get("execution_safety") if isinstance(cfg.get("execution_safety"), dict) else {}

    exchange_id = str(live.get("exchange_id") or "").strip().lower()
    if not exchange_id:
        raise RuntimeError("CBP_CONFIG_REQUIRED:missing_config:live.exchange_id")

    symbols = cfg.get("symbols") or []
    symbol = str(symbols[0]).strip() if symbols else ""
    if not symbol:
        raise RuntimeError("CBP_CONFIG_REQUIRED:missing_config:symbols[0]")

    out = LiveCfg(
        enabled=_boolish(ex_cfg.get("live_enabled", live.get("enabled", False)), default=False),
        observe_only=_boolish(live.get("observe_only", live.get("shadow_mode", False)), default=False),
        sandbox=bool(live.get("sandbox", False)),
        exchange_id=exchange_id,
        exec_db=str(ex_cfg.get("db_path") or (data_dir() / "execution.sqlite")),
        symbol=symbol,
        max_submit_per_tick=int(live.get("max_submit_per_tick") or 1),
        reconcile_limit=int(live.get("reconcile_limit") or 25),
        reconcile_trades=_boolish(live.get("reconcile_trades", True), default=True),
        reconcile_lookback_ms=int(live.get("reconcile_lookback_ms") or ex_cfg.get("live_reconcile_lookback_ms") or (6 * 60 * 60 * 1000)),
        reconcile_trades_limit=int(live.get("reconcile_limit_trades") or ex_cfg.get("live_reconcile_limit_trades") or 200),
    )
    _record_execution_metric(
        name="live_cfg_load_ms",
        value_ms=_measure_ms(started),
        meta={"cfg_path": str(path), "exchange": exchange_id, "symbol": symbol},
        latency_db_path=str(sec.get("latency_db_path") or (data_dir() / "market_ws.sqlite")),
    )
    return out


def _is_live_shadow(cfg: LiveCfg) -> bool:
    if _truthy(os.environ.get("CBP_LIVE_SHADOW"), default=False):
        return True
    return bool(getattr(cfg, "observe_only", False))


def _hard_off_guard(cfg: LiveCfg, *, operation: str = "submit") -> tuple[bool, str]:
    op = str(operation or "submit").strip().lower()
    observe_only = _is_live_shadow(cfg)
    if op == "submit" and observe_only:
        return False, "LIVE_SHADOW observe-only mode: submissions disabled"
    if not cfg.enabled and not observe_only:
        return False, "execution.live_enabled is false"
    if op == "reconcile" and observe_only:
        return True, "ok_shadow"
    armed, reason = live_armed_signal()
    if not armed:
        return False, reason
    return True, "ok"


def _system_guard_submit_open() -> tuple[bool, str, dict[str, Any]]:
    state = dict(get_system_guard_state(fail_closed=True) or {})
    guard_state = str(state.get("state") or "").upper().strip()
    if guard_state in {"HALTING", "HALTED"}:
        return False, f"SYSTEM_GUARD_{guard_state}", state
    return True, "ok", state

def _list_intents_any(store: ExecutionStore, *, mode: str, exchange: str, symbol: str, statuses: list[str], limit: int) -> list[dict[str, Any]]:
    # ExecutionStore.list_intents only supports one status; do multiple queries
    out: list[dict[str, Any]] = []
    for st in statuses:
        out.extend(store.list_intents(mode=mode, exchange=exchange, symbol=symbol, status=st, limit=limit))
    # sort by ts desc
    out.sort(key=lambda r: int(r.get("ts_ms") or 0), reverse=True)
    return out[:limit]


def _local_gate_price(cfg: "LiveCfg", *, side: str) -> float | None:
    quote = get_best_bid_ask_last(cfg.exchange_id, cfg.symbol)
    if not isinstance(quote, dict):
        return None
    side_v = str(side or "").lower().strip()
    if side_v == "buy":
        raw = quote.get("ask")
    else:
        raw = quote.get("bid")
    if raw is None:
        raw = quote.get("last")
    try:
        px = float(raw)
    except Exception:
        return None
    return px if px > 0.0 else None


def _open_reconcile_session(client: Any) -> tuple[Any, bool]:
    build = getattr(client, "build", None)
    if callable(build):
        return build(), True
    return client, False


def _close_reconcile_session(session: Any, *, owned: bool) -> None:
    if not owned:
        return
    try:
        if hasattr(session, "close"):
            session.close()
    except Exception:
        pass


def _fetch_order_for_reconcile(
    client: Any,
    session: Any,
    *,
    owned: bool,
    venue: str,
    symbol: str,
    order_id: str,
) -> dict[str, Any]:
    if owned:
        return fetch_order_via_boundary(
            session,
            venue=venue,
            symbol=symbol,
            order_id=order_id,
            source="live_executor.reconcile_live",
        )
    fetch = getattr(client, "fetch_order")
    return fetch(order_id=order_id, symbol=symbol)


def _fetch_trades_for_reconcile(
    client: Any,
    session: Any,
    *,
    owned: bool,
    venue: str,
    symbol: str,
    since_ms: int | None,
    limit: int,
) -> list[dict[str, Any]]:
    if owned:
        return fetch_my_trades_via_boundary(
            session,
            venue=venue,
            symbol=symbol,
            since_ms=since_ms,
            limit=limit,
            source="live_executor.reconcile_live",
        )
    fetch = getattr(client, "fetch_my_trades")
    return list(fetch(symbol=symbol, since=since_ms, limit=limit) or [])


def _fetch_open_orders_for_reconcile(
    client: Any,
    session: Any,
    *,
    owned: bool,
    venue: str,
    symbol: str,
) -> list[dict[str, Any]]:
    if owned:
        return fetch_open_orders_via_boundary(
            session,
            venue=venue,
            symbol=symbol,
            source="live_executor.reconcile_open_orders",
        )
    fetch = getattr(client, "fetch_open_orders")
    return list(fetch(symbol=symbol) or [])

