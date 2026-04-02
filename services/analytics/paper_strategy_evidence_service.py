from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.admin.config_editor import load_user_yaml
from services.backtest.evidence_cycle import (
    load_paper_history_evidence,
    persist_strategy_evidence,
    run_strategy_evidence_cycle,
    write_decision_record,
)
from services.execution.paper_runner import request_stop as request_paper_engine_stop
from services.market_data.symbol_utils import split_symbol
from services.market_data.symbol_router import normalize_symbol, normalize_venue
from services.market_data.system_status_publisher import request_stop as request_tick_publisher_stop
from services.os.app_paths import code_root, ensure_dirs, runtime_dir
from services.strategy_runner.ema_crossover_runner import request_stop as request_strategy_runner_stop
from storage.position_state_sqlite import PositionStateSQLite

logger = logging.getLogger(__name__)

DEFAULT_STRATEGIES = ("ema_cross", "breakout_donchian", "mean_reversion_rsi")
DEFAULT_VENUE = str(os.environ.get("CBP_VENUE") or "coinbase").strip().lower() or "coinbase"
DEFAULT_SYMBOL = ([item.strip() for item in str(os.environ.get("CBP_SYMBOLS") or "").split(",") if item.strip()] or ["BTC/USD"])[0]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _flags_dir() -> Path:
    return runtime_dir() / "flags"


def _health_dir() -> Path:
    return runtime_dir() / "health"


def stop_file() -> Path:
    return _flags_dir() / "paper_strategy_evidence.stop"


def status_file() -> Path:
    return _health_dir() / "paper_strategy_evidence.json"


def pid_file() -> Path:
    return _health_dir() / "paper_strategy_evidence.pid.json"


def _runtime_files() -> dict[str, dict[str, Path]]:
    return {
        "tick_publisher": {
            "lock_file": runtime_dir() / "locks" / "tick_publisher.lock",
            "status_file": runtime_dir() / "snapshots" / "system_status.latest.json",
        },
        "paper_engine": {
            "lock_file": runtime_dir() / "locks" / "paper_engine.lock",
            "status_file": runtime_dir() / "flags" / "paper_engine.status.json",
        },
        "strategy_runner": {
            "lock_file": runtime_dir() / "locks" / "strategy_runner.lock",
            "status_file": runtime_dir() / "flags" / "strategy_runner.status.json",
        },
    }


def state_dir() -> Path:
    root = os.getenv("CBP_STATE_DIR", "").strip()
    path = Path(root).expanduser().resolve() if root else Path("state").resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path

def _write_status(obj: dict[str, Any]) -> None:
    status = str(obj.get("status") or "").strip().upper()
    if status == "PROMOTED":
        raise ValueError("direct status mutation is not allowed")
    target = status_file()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")
def _write_pid_state(obj: dict[str, Any]) -> None:
    ensure_dirs()
    _health_dir().mkdir(parents=True, exist_ok=True)
    pid_file().write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    return dict(json.loads(path.read_text(encoding="utf-8")) or {})


def _clear_pid_state() -> None:
    try:
        if pid_file().exists():
            pid_file().unlink()
    except Exception as exc:
        logger.warning("paper_strategy_evidence_pid_clear_failed", extra={"error_type": type(exc).__name__, "path": str(pid_file())})


def _process_alive(pid: int) -> bool:
    try:
        os.kill(int(pid), 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except Exception:
        return False


def _strategy_list(raw: Any) -> tuple[str, ...]:
    if isinstance(raw, str):
        values = [item.strip() for item in raw.split(",") if item.strip()]
    else:
        values = [str(item).strip() for item in list(raw or []) if str(item).strip()]
    canonical = [item for item in values if item]
    return tuple(canonical or DEFAULT_STRATEGIES)


def request_stop() -> dict[str, Any]:
    ensure_dirs()
    _flags_dir().mkdir(parents=True, exist_ok=True)
    stop_file().write_text(_now_iso() + "\n", encoding="utf-8")
    return {"ok": True, "stop_file": str(stop_file())}


def _component_runtime(name: str) -> dict[str, Any]:
    meta = _runtime_files()[name]
    lock_file = meta["lock_file"]
    state: dict[str, Any] = {
        "name": name,
        "has_lock": bool(lock_file.exists()),
        "pid": None,
        "pid_alive": False,
        "has_status": False,
        "status": "not_started",
    }
    if lock_file.exists():
        try:
            lock_payload = _load_json(lock_file)
            pid = int(lock_payload.get("pid") or 0)
            if pid > 0:
                state["pid"] = pid
                state["pid_alive"] = _process_alive(pid)
        except Exception as exc:
            state["lock_reason"] = f"lock_read_failed:{type(exc).__name__}"

    status_path = meta["status_file"]
    if status_path.exists():
        try:
            payload = _load_json(status_path)
            state["has_status"] = True
            state["status_payload"] = payload
            payload_status = str(payload.get("status") or "").strip()
            if payload_status:
                state["status"] = payload_status
            if name == "tick_publisher":
                state["snapshot_ts"] = str(payload.get("ts") or "")
        except Exception as exc:
            state["status_reason"] = f"status_read_failed:{type(exc).__name__}"

    if bool(state.get("pid_alive")):
        if state["status"] == "not_started":
            state["status"] = "running"
    elif bool(state.get("has_lock")):
        state["status"] = "dead"
        state["reason"] = "process_not_running"
    elif bool(state.get("has_status")) and state["status"] == "running":
        state["status"] = "dead"
        state["reason"] = "process_not_running"

    return state


def load_runtime_status() -> dict[str, Any]:
    payload: dict[str, Any]
    if status_file().exists():
        try:
            payload = _load_json(status_file())
        except Exception as exc:
            return {
                "ok": False,
                "has_status": False,
                "reason": f"status_read_failed:{type(exc).__name__}",
                "summary_text": "Paper strategy evidence runtime status is unavailable.",
            }
    else:
        payload = {
            "ok": True,
            "has_status": False,
            "status": "not_started",
            "reason": "status_missing",
            "summary_text": "Paper strategy evidence collector has not written runtime status yet.",
        }

    pid_state: dict[str, Any] = {}
    if pid_file().exists():
        try:
            pid_state = _load_json(pid_file())
        except Exception as exc:
            payload["pid_reason"] = f"pid_read_failed:{type(exc).__name__}"
    pid = int(pid_state.get("pid") or 0) if pid_state else 0
    pid_alive = _process_alive(pid) if pid > 0 else False

    payload["ok"] = bool(payload.get("ok", True))
    payload["has_status"] = bool(payload.get("has_status")) if "has_status" in payload else True
    payload["pid"] = pid or None
    payload["pid_alive"] = pid_alive
    payload["has_pid_file"] = bool(pid_state)
    payload["started_ts"] = str(pid_state.get("started_ts") or "")
    payload["strategies"] = list(payload.get("strategies") or pid_state.get("strategies") or [])
    payload["symbol"] = str(payload.get("symbol") or pid_state.get("symbol") or DEFAULT_SYMBOL)
    payload["venue"] = str(payload.get("venue") or pid_state.get("venue") or DEFAULT_VENUE)
    payload["per_strategy_runtime_sec"] = float(
        payload.get("per_strategy_runtime_sec") or pid_state.get("per_strategy_runtime_sec") or 0.0
    )

    if pid_state and payload.get("status") == "running" and not pid_alive:
        payload["status"] = "dead"
        payload["reason"] = "process_not_running"
    elif pid_state and not payload.get("has_status") and pid_alive:
        payload["status"] = "starting"
        payload["reason"] = "pid_alive_waiting_for_status"
        payload["has_status"] = True

    return payload


def _strategy_summary_map(journal_path: str = "", *, symbol: str = "") -> dict[str, dict[str, Any]]:
    payload = load_paper_history_evidence(journal_path=journal_path, symbol=symbol)
    return {
        str(row.get("strategy") or ""): dict(row)
        for row in list(payload.get("rows") or [])
        if str(row.get("strategy") or "").strip()
    }


def _strategy_delta(
    strategy_name: str,
    *,
    before_rows: dict[str, dict[str, Any]],
    after_rows: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    before = dict(before_rows.get(strategy_name) or {})
    after = dict(after_rows.get(strategy_name) or {})
    fills_before = int(before.get("fills") or 0)
    fills_after = int(after.get("fills") or 0)
    closed_before = int(before.get("closed_trades") or 0)
    closed_after = int(after.get("closed_trades") or 0)
    pnl_before = float(before.get("net_realized_pnl") or 0.0)
    pnl_after = float(after.get("net_realized_pnl") or 0.0)
    return {
        "fills_delta": int(fills_after - fills_before),
        "closed_trades_delta": int(closed_after - closed_before),
        "net_realized_pnl_delta": float(pnl_after - pnl_before),
        "fills_total": int(fills_after),
        "closed_trades_total": int(closed_after),
        "net_realized_pnl_total": float(pnl_after),
        "latest_fill_ts": str(after.get("latest_fill_ts") or ""),
    }


def _campaign_has_new_paper_history(results: list[dict[str, Any]]) -> bool:
    for item in results:
        if int(item.get("fills_delta") or 0) > 0:
            return True
        if int(item.get("closed_trades_delta") or 0) > 0:
            return True
    return False


def _repo_script_path(script_relpath: str) -> str:
    return str((code_root() / script_relpath).resolve())


def _start_process(*, script_relpath: str, env: dict[str, str]) -> subprocess.Popen[Any]:
    kwargs: dict[str, Any] = {
        "cwd": str(code_root()),
        "env": env,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "stdin": subprocess.DEVNULL,
    }
    if os.name == "nt":
        creationflags = 0
        if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
            creationflags |= subprocess.CREATE_NEW_PROCESS_GROUP
        if hasattr(subprocess, "DETACHED_PROCESS"):
            creationflags |= subprocess.DETACHED_PROCESS
        kwargs["creationflags"] = creationflags
    else:
        kwargs["start_new_session"] = True
    return subprocess.Popen([sys.executable, _repo_script_path(script_relpath)], **kwargs)


def _wait_for(predicate, *, timeout_sec: float, sleep_sec: float = 0.2) -> bool:
    deadline = time.time() + max(0.0, float(timeout_sec))
    while time.time() <= deadline:
        if predicate():
            return True
        time.sleep(max(0.05, float(sleep_sec)))
    return bool(predicate())


def _component_env(cfg: "PaperStrategyEvidenceServiceCfg", *, strategy_name: str | None = None) -> dict[str, str]:
    env = dict(os.environ)
    env["CBP_SYMBOLS"] = str(cfg.symbol or DEFAULT_SYMBOL)
    env["CBP_VENUE"] = str(cfg.venue or DEFAULT_VENUE)
    env["CBP_TICK_PUBLISH_INTERVAL_SEC"] = str(float(cfg.tick_publish_interval_sec))
    if int(cfg.strategy_min_bars or 0) > 0:
        env["CBP_STRATEGY_MIN_BARS"] = str(int(cfg.strategy_min_bars))
    if str(cfg.signal_source or "").strip():
        env["CBP_STRATEGY_SIGNAL_SOURCE"] = str(cfg.signal_source).strip()
    if bool(cfg.allow_first_signal_trade):
        env["CBP_STRATEGY_ALLOW_FIRST_SIGNAL_TRADE"] = "1"
    if strategy_name:
        env["CBP_STRATEGY_NAME"] = str(strategy_name)
    return env


def _target_symbols(cfg: "PaperStrategyEvidenceServiceCfg") -> list[str]:
    raw = [str(item).strip() for item in str(cfg.symbol or DEFAULT_SYMBOL).split(",") if str(item).strip()]
    out: list[str] = []
    seen: set[str] = set()
    for item in raw or [DEFAULT_SYMBOL]:
        sym = normalize_symbol(item)
        if sym and sym not in seen:
            out.append(sym)
            seen.add(sym)
    return out


def _ensure_known_flat_position_state(*, venue: str, symbol: str) -> dict[str, Any]:
    v = normalize_venue(venue)
    sym = normalize_symbol(symbol)
    store = PositionStateSQLite()
    row = store.get(venue=v, symbol=sym)
    if row is not None:
        return {
            "ok": True,
            "seeded": False,
            "venue": v,
            "symbol": sym,
            "reason": "position_state_exists",
            "row": row,
        }

    base, quote = split_symbol(sym)
    if not base or not quote:
        return {
            "ok": False,
            "seeded": False,
            "venue": v,
            "symbol": sym,
            "reason": "symbol_parse_failed",
        }

    seeded_row = {
        "venue": v,
        "symbol": sym,
        "base": base,
        "quote": quote,
        "qty": 0.0,
        "status": "flat",
        "note": "seeded_for_managed_paper_campaign",
        "raw": {
            "seeded_by": "paper_strategy_evidence_service",
            "seed_reason": "managed_campaign_startup_guard",
        },
    }
    store.upsert(**seeded_row)
    return {
        "ok": True,
        "seeded": True,
        "venue": v,
        "symbol": sym,
        "reason": "missing_row_seeded_flat",
        "row": store.get(venue=v, symbol=sym) or seeded_row,
    }


def _tick_publisher_reusable(state: dict[str, Any], *, cfg: "PaperStrategyEvidenceServiceCfg") -> bool:
    payload = state.get("status_payload") if isinstance(state.get("status_payload"), dict) else {}
    venue = normalize_venue(str(cfg.venue or DEFAULT_VENUE))
    symbols = set(_target_symbols(cfg))
    venues = payload.get("venues") if isinstance(payload.get("venues"), dict) else {}
    venue_row = venues.get(venue) if isinstance(venues.get(venue), dict) else {}
    if not venue_row or not bool(venue_row.get("ok")):
        return False
    ticks = payload.get("ticks")
    if not isinstance(ticks, list):
        return False
    now_ms = int(time.time() * 1000)
    max_age_ms = max(10_000, int(max(0.5, float(cfg.tick_publish_interval_sec or 2.0)) * 4000))
    fresh_symbols: set[str] = set()
    for tick in ticks:
        if not isinstance(tick, dict):
            continue
        if normalize_venue(str(tick.get("venue") or "")) != venue:
            continue
        symbol = normalize_symbol(str(tick.get("symbol") or ""))
        if symbol not in symbols:
            continue
        ts_ms = int(tick.get("ts_ms") or 0)
        if ts_ms <= 0:
            continue
        if (now_ms - ts_ms) > max_age_ms:
            continue
        fresh_symbols.add(symbol)
    return symbols.issubset(fresh_symbols)


def _ensure_component(name: str, *, cfg: "PaperStrategyEvidenceServiceCfg") -> dict[str, Any]:
    current = _component_runtime(name)
    if bool(current.get("pid_alive")):
        if name == "tick_publisher" and not _tick_publisher_reusable(current, cfg=cfg):
            try:
                _stop_component(name)
            except Exception as exc:
                logger.warning("paper_strategy_evidence_tick_reuse_stop_failed", extra={"error_type": type(exc).__name__})
            _wait_for_component_stop(name, timeout_sec=10.0)
            current = _component_runtime(name)
        else:
            return {
                "name": name,
                "started": False,
                "pid": int(current.get("pid") or 0),
                "status": str(current.get("status") or "running"),
            }

    script = {
        "tick_publisher": "scripts/run_tick_publisher.py",
        "paper_engine": "scripts/run_paper_engine.py",
    }.get(name)
    if not script:
        raise ValueError(f"unsupported component: {name}")

    proc = _start_process(script_relpath=script, env=_component_env(cfg))
    ok = _wait_for(
        lambda: bool(_component_runtime(name).get("pid_alive")) or (proc.poll() is not None),
        timeout_sec=5.0,
        sleep_sec=0.2,
    )
    state = _component_runtime(name)
    if not ok or proc.poll() not in {None} and not bool(state.get("pid_alive")):
        raise RuntimeError(f"{name}_failed_to_start")
    return {
        "name": name,
        "started": True,
        "pid": int(proc.pid),
        "status": str(state.get("status") or "running"),
    }


def _stop_component(name: str) -> dict[str, Any]:
    if name == "tick_publisher":
        return dict(request_tick_publisher_stop())
    if name == "paper_engine":
        return dict(request_paper_engine_stop())
    if name == "strategy_runner":
        return dict(request_strategy_runner_stop())
    raise ValueError(f"unsupported component: {name}")


def _wait_for_component_stop(name: str, *, timeout_sec: float = 10.0) -> bool:
    return _wait_for(lambda: not bool(_component_runtime(name).get("pid_alive")), timeout_sec=timeout_sec, sleep_sec=0.2)


def _run_strategy_window(
    *,
    cfg: "PaperStrategyEvidenceServiceCfg",
    strategy_name: str,
) -> dict[str, Any]:
    before_rows = _strategy_summary_map(cfg.paper_history_path, symbol=str(cfg.symbol or DEFAULT_SYMBOL))
    proc = _start_process(
        script_relpath="scripts/run_strategy_runner.py",
        env=_component_env(cfg, strategy_name=strategy_name),
    )

    started = _wait_for(
        lambda: bool(_component_runtime("strategy_runner").get("pid_alive")) or proc.poll() is not None,
        timeout_sec=5.0,
        sleep_sec=0.2,
    )
    if not started or proc.poll() not in {None} and not bool(_component_runtime("strategy_runner").get("pid_alive")):
        raise RuntimeError(f"strategy_runner_failed_to_start:{strategy_name}")

    started_ts = _now_iso()
    loop_started_at = time.time()
    last_status = _component_runtime("strategy_runner").get("status_payload") or {}
    stop_reason = "runtime_elapsed"
    try:
        while (time.time() - loop_started_at) < float(cfg.per_strategy_runtime_sec):
            if stop_file().exists():
                stop_reason = "stop_requested"
                break
            if proc.poll() is not None and not bool(_component_runtime("strategy_runner").get("pid_alive")):
                stop_reason = f"runner_exited:{int(proc.returncode or 0)}"
                break
            runner_state = _component_runtime("strategy_runner")
            last_status = dict(runner_state.get("status_payload") or last_status or {})
            time.sleep(0.5)
    finally:
        try:
            _stop_component("strategy_runner")
        except Exception as exc:
            logger.warning("strategy_runner_stop_failed", extra={"strategy": strategy_name, "error_type": type(exc).__name__})
        _wait_for_component_stop("strategy_runner", timeout_sec=10.0)
        time.sleep(max(0.0, float(cfg.strategy_drain_sec)))

    after_rows = _strategy_summary_map(cfg.paper_history_path, symbol=str(cfg.symbol or DEFAULT_SYMBOL))
    delta = _strategy_delta(strategy_name, before_rows=before_rows, after_rows=after_rows)
    ended_ts = _now_iso()
    last_status = dict((_component_runtime("strategy_runner").get("status_payload") or last_status or {}))
    return {
        "strategy": str(strategy_name),
        "started_ts": started_ts,
        "ended_ts": ended_ts,
        "runtime_sec": max(time.time() - loop_started_at, 0.0),
        "stop_reason": stop_reason,
        "runner_status": str(last_status.get("status") or "stopped"),
        "runner_note": str(last_status.get("note") or ""),
        "signal_action": str(last_status.get("signal_action") or ""),
        "signal_changed": bool(last_status.get("signal_changed")),
        "enqueued_total": int(last_status.get("enqueued_total") or 0),
        "fills_delta": int(delta["fills_delta"]),
        "closed_trades_delta": int(delta["closed_trades_delta"]),
        "net_realized_pnl_delta": float(delta["net_realized_pnl_delta"]),
        "fills_total": int(delta["fills_total"]),
        "closed_trades_total": int(delta["closed_trades_total"]),
        "net_realized_pnl_total": float(delta["net_realized_pnl_total"]),
        "latest_fill_ts": str(delta["latest_fill_ts"] or ""),
    }


def _summary_text(payload: dict[str, Any]) -> str:
    def _runner_note_summary(note: str, *, strategy_name: str = "") -> str:
        raw = str(note or "").strip()
        if not raw.startswith("no_fresh_tick:"):
            return ""
        target = f" for {strategy_name}" if strategy_name else ""
        mapping = {
            "no_fresh_tick:snapshot_file_missing:start_tick_publisher": (
                f"Strategy runner is waiting for fresh market ticks{target}; start the tick publisher."
            ),
            "no_fresh_tick:snapshot_stale:publisher_stopped_or_network_blocked": (
                f"Strategy runner is waiting for fresh market ticks{target}; the tick snapshot is stale, so the publisher may be stopped or network access may be blocked."
            ),
            "no_fresh_tick:snapshot_unreadable:check_tick_publisher_output": (
                f"Strategy runner is waiting for fresh market ticks{target}; the tick snapshot could not be read, so check tick publisher output."
            ),
            "no_fresh_tick:snapshot_has_no_ticks:check_venue_connectivity": (
                f"Strategy runner is waiting for fresh market ticks{target}; the snapshot has no usable ticks, so check venue connectivity."
            ),
            "no_fresh_tick:snapshot_present_but_symbol_missing:check_symbol_or_venue_mapping": (
                f"Strategy runner is waiting for fresh market ticks{target}; the snapshot is fresh but the requested symbol is missing, so check symbol or venue mapping."
            ),
        }
        return mapping.get(raw, "")

    def _latest_runner_note(obj: dict[str, Any]) -> tuple[str, str]:
        note = str(obj.get("runner_note") or "").strip()
        strategy_name = str(obj.get("current_strategy") or obj.get("strategy") or "").strip()
        if note:
            return note, strategy_name
        rows = list(obj.get("results") or [])
        for row in reversed(rows):
            if not isinstance(row, dict):
                continue
            row_note = str(row.get("runner_note") or "").strip()
            if row_note:
                return row_note, str(row.get("strategy") or strategy_name or "").strip()
        return "", strategy_name

    status = str(payload.get("status") or "unknown").replace("_", " ")
    current = str(payload.get("current_strategy") or "").strip()
    completed = int(payload.get("completed_strategies") or 0)
    total = int(payload.get("total_strategies") or 0)
    runner_note, runner_strategy = _latest_runner_note(payload)
    runner_summary = _runner_note_summary(runner_note, strategy_name=(current or runner_strategy))
    if current:
        base = f"Paper evidence collector is {status} on {current} ({completed}/{total} complete)."
        return f"{base} {runner_summary}".strip() if runner_summary else base
    if total > 0:
        base = f"Paper evidence collector is {status} ({completed}/{total} complete)."
        return f"{base} {runner_summary}".strip() if runner_summary else base
    base = f"Paper evidence collector is {status}."
    return f"{base} {runner_summary}".strip() if runner_summary else base


@dataclass(frozen=True)
class PaperStrategyEvidenceServiceCfg:
    strategies: tuple[str, ...] = DEFAULT_STRATEGIES
    per_strategy_runtime_sec: float = 900.0
    strategy_drain_sec: float = 2.0
    symbol: str = DEFAULT_SYMBOL
    venue: str = DEFAULT_VENUE
    tick_publish_interval_sec: float = 2.0
    strategy_min_bars: int = 0
    signal_source: str = ""
    allow_first_signal_trade: bool = False
    evidence_symbol: str = ""
    initial_cash: float = 10_000.0
    fee_bps: float = 10.0
    slippage_bps: float = 5.0
    paper_history_path: str = ""
    write_decision_record: bool = True


def run_campaign(cfg: PaperStrategyEvidenceServiceCfg, *, max_strategies: int | None = None) -> dict[str, Any]:
    ensure_dirs()
    current_pid = int(os.getpid())
    existing = load_runtime_status()
    if bool(existing.get("pid_alive")) and int(existing.get("pid") or 0) not in {0, current_pid}:
        return {
            "ok": True,
            "status": "running",
            "reason": "already_running",
            "pid": int(existing.get("pid") or 0),
            "strategies": list(existing.get("strategies") or []),
        }

    strategy_runner_state = _component_runtime("strategy_runner")
    if bool(strategy_runner_state.get("pid_alive")) and int(strategy_runner_state.get("pid") or 0) not in {0, current_pid}:
        out = {
            "ok": False,
            "status": "blocked",
            "reason": "strategy_runner_busy",
            "pid": int(strategy_runner_state.get("pid") or 0),
            "summary_text": "Strategy runner is already active, so managed paper evidence collection cannot take ownership safely.",
        }
        _write_status(out)
        return out

    strategies = list(_strategy_list(cfg.strategies))
    if max_strategies is not None and int(max_strategies) > 0:
        strategies = strategies[: int(max_strategies)]

    try:
        if stop_file().exists():
            stop_file().unlink()
    except Exception as exc:
        logger.warning("paper_strategy_evidence_stop_file_clear_failed", extra={"error_type": type(exc).__name__, "path": str(stop_file())})

    _write_pid_state(
        {
            "pid": current_pid,
            "started_ts": _now_iso(),
            "strategies": strategies,
            "symbol": str(cfg.symbol or DEFAULT_SYMBOL),
            "venue": str(cfg.venue or DEFAULT_VENUE),
            "per_strategy_runtime_sec": float(cfg.per_strategy_runtime_sec),
        }
    )

    started_components: dict[str, int] = {}
    reused_components: dict[str, int] = {}
    results: list[dict[str, Any]] = []
    campaign_reason = "completed"
    evidence_out: dict[str, Any] = {}
    decision_record_out: dict[str, Any] = {}

    _write_status(
        {
            "ok": True,
            "has_status": True,
            "status": "starting",
            "reason": "initializing",
            "ts": _now_iso(),
            "pid": current_pid,
            "strategies": strategies,
            "completed_strategies": 0,
            "total_strategies": len(strategies),
            "symbol": str(cfg.symbol or DEFAULT_SYMBOL),
            "venue": str(cfg.venue or DEFAULT_VENUE),
            "per_strategy_runtime_sec": float(cfg.per_strategy_runtime_sec),
            "started_components": {},
            "reused_components": {},
        }
    )

    try:
        for name in ("tick_publisher", "paper_engine"):
            comp = _ensure_component(name, cfg=cfg)
            if bool(comp.get("started")):
                started_components[name] = int(comp.get("pid") or 0)
            else:
                reused_components[name] = int(comp.get("pid") or 0)

        for idx, strategy_name in enumerate(strategies, start=1):
            if stop_file().exists():
                campaign_reason = "stop_requested"
                break
            seeded_state = _ensure_known_flat_position_state(
                venue=str(cfg.venue or DEFAULT_VENUE),
                symbol=str(cfg.symbol or DEFAULT_SYMBOL),
            )
            if not bool(seeded_state.get("ok")):
                raise RuntimeError(
                    f"position_state_seed_failed:{seeded_state.get('reason') or 'unknown'}"
                )
            _write_status(
                {
                    "ok": True,
                    "has_status": True,
                    "status": "running",
                    "reason": "collecting",
                    "ts": _now_iso(),
                    "pid": current_pid,
                    "strategies": strategies,
                    "current_strategy": str(strategy_name),
                    "completed_strategies": len(results),
                    "total_strategies": len(strategies),
                    "symbol": str(cfg.symbol or DEFAULT_SYMBOL),
                    "venue": str(cfg.venue or DEFAULT_VENUE),
                    "per_strategy_runtime_sec": float(cfg.per_strategy_runtime_sec),
                    "started_components": started_components,
                    "reused_components": reused_components,
                    "results": results,
                    "summary_text": _summary_text(
                        {
                            "status": "running",
                            "current_strategy": strategy_name,
                            "completed_strategies": len(results),
                            "total_strategies": len(strategies),
                        }
                    ),
                }
            )
            result = _run_strategy_window(cfg=cfg, strategy_name=strategy_name)
            stop_reason = str(result.get("stop_reason") or "").strip().lower()
            if stop_reason in {"fingerprint_mismatch", "drift", "contamination"}:
                out = {
                    "ok": True,
                    "has_status": True,
                    "status": "INVALID",
                    "is_terminal": True,
                    "reason": stop_reason,
                    "ts": _now_iso(),
                    "pid": current_pid,
                    "strategy": str(strategy_name),
                    "completed_strategies": idx - 1,
                    "total_strategies": len(strategies),
                    "symbol": str(cfg.symbol or DEFAULT_SYMBOL),
                    "venue": str(cfg.venue or DEFAULT_VENUE),
                    "per_strategy_runtime_sec": float(cfg.per_strategy_runtime_sec),
                    "started_components": dict(started_components),
                    "reused_components": dict(reused_components),
                }
                _write_status(out)
                return out
            results.append(result)
            if result.get("stop_reason") == "stop_requested":
                campaign_reason = "stop_requested"
                break

        for name in reversed(tuple(started_components.keys())):
            try:
                _stop_component(name)
            except Exception as exc:
                logger.warning("paper_strategy_evidence_component_stop_failed", extra={"component": name, "error_type": type(exc).__name__})
        for name in reversed(tuple(started_components.keys())):
            _wait_for_component_stop(name, timeout_sec=10.0)

        if _campaign_has_new_paper_history(results):
            report = run_strategy_evidence_cycle(
                base_cfg=load_user_yaml(),
                symbol=str(cfg.evidence_symbol or cfg.symbol or DEFAULT_SYMBOL),
                initial_cash=float(cfg.initial_cash),
                fee_bps=float(cfg.fee_bps),
                slippage_bps=float(cfg.slippage_bps),
                paper_history_path=str(cfg.paper_history_path or ""),
            )
            evidence_out = persist_strategy_evidence(report)
            if bool(cfg.write_decision_record):
                decision_record_out = write_decision_record(
                    report,
                    artifact_path=str(evidence_out.get("latest_path") or ""),
                )
        else:
            evidence_out = {
                "ok": True,
                "skipped": True,
                "reason": "paper_history_unchanged",
                "summary_text": (
                    "No new paper-history fills or closed trades were recorded during the campaign, "
                    "so the evidence cycle was skipped."
                ),
            }
            if bool(cfg.write_decision_record):
                decision_record_out = {
                    "ok": True,
                    "skipped": True,
                    "reason": "paper_history_unchanged",
                    "summary_text": "Decision record was not regenerated because paper-history coverage did not change.",
                }
    except Exception as exc:
        campaign_reason = f"error:{type(exc).__name__}"
        out = {
            "ok": False,
            "has_status": True,
            "status": "failed",
            "reason": campaign_reason,
            "ts": _now_iso(),
            "pid": current_pid,
            "strategies": strategies,
            "completed_strategies": len(results),
            "total_strategies": len(strategies),
            "current_strategy": str(results[-1].get("strategy") or "") if results else "",
            "symbol": str(cfg.symbol or DEFAULT_SYMBOL),
            "venue": str(cfg.venue or DEFAULT_VENUE),
            "per_strategy_runtime_sec": float(cfg.per_strategy_runtime_sec),
            "started_components": started_components,
            "reused_components": reused_components,
            "results": results,
            "summary_text": "Paper strategy evidence collector failed before completing the campaign.",
        }
        _write_status(out)
        raise
    finally:
        try:
            _stop_component("strategy_runner")
        except Exception:
            pass
        _wait_for_component_stop("strategy_runner", timeout_sec=2.0)
        _clear_pid_state()

    out = {
        "ok": True,
        "has_status": True,
        "status": "stopped" if campaign_reason == "stop_requested" else "completed",
        "reason": campaign_reason,
        "ts": _now_iso(),
        "pid": current_pid,
        "strategies": strategies,
        "completed_strategies": len(results),
        "total_strategies": len(strategies),
        "symbol": str(cfg.symbol or DEFAULT_SYMBOL),
        "venue": str(cfg.venue or DEFAULT_VENUE),
        "per_strategy_runtime_sec": float(cfg.per_strategy_runtime_sec),
        "started_components": started_components,
        "reused_components": reused_components,
        "results": results,
        "evidence": evidence_out,
        "decision_record": decision_record_out,
    }
    out["summary_text"] = _summary_text(out)
    _write_status(out)
    return out
