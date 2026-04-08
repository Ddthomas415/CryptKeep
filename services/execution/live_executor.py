from __future__ import annotations
from services.risk.market_quality_guard import check_market_quality

import os
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from services.admin.system_guard import get_state as get_system_guard_state
from services.execution.live_arming import live_armed_signal
from services.execution.client_order_id import make_client_order_id
from services.execution.execution_latency import ExecutionLatencyTracker
from services.execution.lifecycle_boundary import (
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

def _load_yaml_cached(path: str) -> dict:
    """Load a YAML file with mtime-based cache."""
    p = Path(path)
    try:
        mtime = p.stat().st_mtime
    except FileNotFoundError:
        return {}
    cached = _yaml_cache.get(path)
    if cached is not None and cached[0] == mtime:
        return cached[1]
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except Exception:
        data = {}
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
    cfg = _load_yaml_cached(cfg_path)
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
    cfg = yaml.safe_load(open(path, "r", encoding="utf-8").read()) or {}
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
        enabled=bool(live.get("enabled", False)),
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
        return False, "live.enabled is false"
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
    _cfg_cached = _load_yaml_cached('config/trading.yaml')
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

        _sym_lock = store.get_symbol_lock(str(it.get("symbol") or ""))
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
            except Exception:
                pass

            # EXEC_GUARD_TRADE_ATTEMPT
            try:
                from storage.execution_guard_store_sqlite import ExecutionGuardStoreSQLite
                ExecutionGuardStoreSQLite()._record_trade_attempt_sync()
            except Exception:
                pass
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
                        except Exception:
                            pass

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
                        except Exception:
                            pass
                store.set_intent_status(intent_id=intent_id, status="filled", reason=f"remote_id={remote_id}")

                try:
                    store_dedupe.mark_terminal(exchange_id=cfg.exchange_id, intent_id=intent_id, terminal_status=status)
                except Exception:
                    pass
            elif status in ("canceled", "cancelled", "rejected", "expired"):
                store.set_intent_status(intent_id=intent_id, status="canceled", reason=f"remote_id={remote_id}:{status}")
                try:
                    store_dedupe.mark_terminal(exchange_id=cfg.exchange_id, intent_id=intent_id, terminal_status=status)
                except Exception:
                    pass
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

def reconcile_open_orders(exec_db: str, exchange_id: str, *, limit: int = 200) -> dict:
    ex_id = (exchange_id or "").lower().strip()
    store = OrderDedupeStore(exec_db=exec_db)
    client = ExchangeClient(exchange_id=ex_id, sandbox=False)
    rows = store.list_needs_reconcile(exchange_id=ex_id, limit=int(limit))
    by_sym = {}
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
            oo = client.fetch_open_orders(symbol=sym) or []
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
