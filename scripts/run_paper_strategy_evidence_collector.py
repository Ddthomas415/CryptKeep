#!/usr/bin/env python3
from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

import argparse
import json
import logging
import os
import subprocess
import time
from datetime import datetime, timezone

from services.analytics.paper_strategy_evidence_service import (
    PaperStrategyEvidenceServiceCfg,
    _clear_pid_state,
    _write_pid_state,
    _write_status,
    load_runtime_status,
    request_stop,
    run_campaign,
    stop_file,
)
from services.admin.kill_switch import get_state as get_kill_switch_state
from services.control.deployment_stage import get_current_stage
from services.os.app_paths import data_dir, runtime_dir
from services.strategies.evidence_logger import EvidenceLogger

_DEFAULT_SESSION_STRATEGY_ID_BY_STRATEGY = {
    "sma_200_trend": "es_daily_trend_v1",
    "ema_cross": "ema_cross_default",
    "mean_reversion_rsi": "mean_reversion_default",
    "breakout_donchian": "breakout_default",
    "momentum": "momentum_default",
    "volatility_reversal": "volatility_reversal_default",
    "gap_fill": "gap_fill_default",
    "breakout_volume": "breakout_volume_default",
}
_LOG = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today_utc() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _strategy_items(raw: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in str(raw or "").split(",") if item.strip())


def _session_strategy_id(*, strategies: tuple[str, ...], override: str = "") -> str:
    explicit = str(override or "").strip()
    if explicit:
        return explicit
    first = str(strategies[0] if strategies else "paper_strategy_evidence").strip()
    return _DEFAULT_SESSION_STRATEGY_ID_BY_STRATEGY.get(first, first or "paper_strategy_evidence")


def _default_signal_source(*, strategies: tuple[str, ...], requested: str = "") -> str:
    explicit = str(requested or "").strip()
    if explicit:
        return explicit
    if any(str(item or "").strip() == "sma_200_trend" for item in strategies):
        return "public_ohlcv_1d"
    return ""


def _campaign_provenance_extra(cfg: PaperStrategyEvidenceServiceCfg) -> dict[str, object]:
    source = str(cfg.signal_source or "").strip().lower()
    if not source.startswith("public_ohlcv_"):
        return {}
    sample_mode = str(os.environ.get("CBP_USE_SAMPLE_OHLCV") or "").strip().lower() in {"1", "true", "yes", "on"}
    return {
        "market_data_source": "sample_ohlcv" if sample_mode else "public_ohlcv",
        "ohlcv_sample_mode": sample_mode,
        "ohlcv_timeframe": source.removeprefix("public_ohlcv_") or None,
        "ohlcv_venue": str(cfg.venue or ""),
        "ohlcv_symbol": str(cfg.symbol or ""),
    }


def _session_log_path(strategy_id: str, day: str) -> Path:
    return data_dir() / "evidence" / str(strategy_id or "").strip() / f"session_{day}.jsonl"


def _has_session_day(strategy_id: str, day: str) -> bool:
    path = _session_log_path(strategy_id, day)
    return path.exists() and path.stat().st_size > 0


def _log_session_start(*, strategy_id: str, cfg: PaperStrategyEvidenceServiceCfg) -> None:
    ev = EvidenceLogger(strategy_id)
    ev.log_session(
        regime_at_open=get_current_stage(strategy_id).value,
        halts_triggered=[],
        manual_overrides=[],
        reconciliation_result="pending",
        drawdown_from_peak=0.0,
        ops_checks_passed=True,
        extra={
            "phase": "start",
            "campaign_status": "starting",
            "completed_strategies": 0,
            "zero_trade_run": True,
            **_campaign_provenance_extra(cfg),
        },
    )


def _log_session_end(*, strategy_id: str, cfg: PaperStrategyEvidenceServiceCfg, result: dict[str, object]) -> None:
    completed = int(result.get("completed_strategies") or 0)
    campaign_status = str(result.get("status") or "unknown")
    ev = EvidenceLogger(strategy_id)
    ev.log_session(
        regime_at_open=get_current_stage(strategy_id).value,
        halts_triggered=list(result.get("halt_reasons") or []),
        manual_overrides=[],
        reconciliation_result="pass" if result.get("ok") else "campaign_error",
        drawdown_from_peak=float(result.get("max_drawdown_pct") or 0.0),
        kill_switch_tested=bool(get_kill_switch_state().get("armed", False)),
        ops_checks_passed=bool(result.get("ok")),
        critical_error=(campaign_status not in ("completed", "stopped", "stop_requested")),
        extra={
            "phase": "end",
            "completed_strategies": completed,
            "campaign_status": campaign_status,
            "zero_trade_run": (completed == 0),
            **_campaign_provenance_extra(cfg),
        },
    )


def _run_one_campaign(
    cfg: PaperStrategyEvidenceServiceCfg,
    *,
    max_strategies: int | None,
    session_strategy_id: str,
) -> dict[str, object]:
    result: dict[str, object] = {"ok": False, "status": "not_started", "completed_strategies": 0}
    try:
        _log_session_start(strategy_id=session_strategy_id, cfg=cfg)
    except Exception as exc:
        _LOG.warning("paper_strategy_evidence_session_start_failed strategy_id=%s error=%s", session_strategy_id, exc)
    try:
        result = run_campaign(cfg, max_strategies=max_strategies)
        return result
    finally:
        try:
            _log_session_end(strategy_id=session_strategy_id, cfg=cfg, result=result)
        except Exception as exc:
            _LOG.warning("paper_strategy_evidence_session_end_failed strategy_id=%s error=%s", session_strategy_id, exc)


def _write_idle_status(
    *,
    pid: int,
    cfg: PaperStrategyEvidenceServiceCfg,
    strategies: tuple[str, ...],
    session_strategy_id: str,
    last_result: dict[str, object] | None = None,
) -> dict[str, object]:
    out: dict[str, object] = {
        "ok": True,
        "has_status": True,
        "status": "idle",
        "reason": "waiting_for_next_day",
        "ts": _now_iso(),
        "pid": int(pid),
        "strategies": list(strategies),
        "completed_strategies": int((last_result or {}).get("completed_strategies") or 0),
        "total_strategies": len(strategies),
        "symbol": str(cfg.symbol or "BTC/USD"),
        "venue": str(cfg.venue or "coinbase"),
        "signal_source": str(cfg.signal_source or ""),
        "per_strategy_runtime_sec": float(cfg.per_strategy_runtime_sec),
        "session_strategy_id": str(session_strategy_id),
        "daily_loop": True,
        "last_completed_day": _today_utc(),
        "summary_text": (
            f"Paper evidence collector is idle; {session_strategy_id} already recorded session evidence for "
            f"{_today_utc()}, waiting for the next UTC day."
        ),
    }
    if isinstance(last_result, dict) and last_result:
        out["last_result"] = dict(last_result)
    _write_status(out)
    return out


def _run_daily_loop(
    cfg: PaperStrategyEvidenceServiceCfg,
    *,
    max_strategies: int | None,
    session_strategy_id: str,
    poll_interval_sec: float,
    max_loops: int | None = None,
) -> dict[str, object]:
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

    try:
        if stop_file().exists():
            stop_file().unlink()
    except Exception:
        pass

    strategies = tuple(cfg.strategies)
    _write_pid_state(
        {
            "pid": current_pid,
            "started_ts": _now_iso(),
            "strategies": list(strategies),
            "symbol": str(cfg.symbol or "BTC/USD"),
            "venue": str(cfg.venue or "coinbase"),
            "signal_source": str(cfg.signal_source or ""),
            "per_strategy_runtime_sec": float(cfg.per_strategy_runtime_sec),
            "poll_interval_sec": float(poll_interval_sec),
            "daily_loop": True,
            "session_strategy_id": str(session_strategy_id),
        }
    )

    loops = 0
    last_result: dict[str, object] = {}
    try:
        while True:
            loops += 1
            if stop_file().exists():
                out: dict[str, object] = {
                    "ok": True,
                    "has_status": True,
                    "status": "stopped",
                    "reason": "stop_requested",
                    "ts": _now_iso(),
                    "pid": current_pid,
                    "strategies": list(strategies),
                    "symbol": str(cfg.symbol or "BTC/USD"),
                    "venue": str(cfg.venue or "coinbase"),
                    "signal_source": str(cfg.signal_source or ""),
                    "per_strategy_runtime_sec": float(cfg.per_strategy_runtime_sec),
                    "session_strategy_id": str(session_strategy_id),
                    "daily_loop": True,
                    "loops": loops,
                    "summary_text": "Paper evidence collector daily loop was stopped by request.",
                }
                if last_result:
                    out["last_result"] = dict(last_result)
                _write_status(out)
                return out

            today = _today_utc()
            if not _has_session_day(session_strategy_id, today):
                last_result = _run_one_campaign(
                    cfg,
                    max_strategies=max_strategies,
                    session_strategy_id=session_strategy_id,
                )
                _write_pid_state(
                    {
                        "pid": current_pid,
                        "started_ts": _now_iso(),
                        "strategies": list(strategies),
                        "symbol": str(cfg.symbol or "BTC/USD"),
                        "venue": str(cfg.venue or "coinbase"),
                        "signal_source": str(cfg.signal_source or ""),
                        "per_strategy_runtime_sec": float(cfg.per_strategy_runtime_sec),
                        "poll_interval_sec": float(poll_interval_sec),
                        "daily_loop": True,
                        "session_strategy_id": str(session_strategy_id),
                    }
                )
                _write_idle_status(
                    pid=current_pid,
                    cfg=cfg,
                    strategies=strategies,
                    session_strategy_id=session_strategy_id,
                    last_result=last_result,
                )
            else:
                _write_idle_status(
                    pid=current_pid,
                    cfg=cfg,
                    strategies=strategies,
                    session_strategy_id=session_strategy_id,
                    last_result=last_result,
                )

            if max_loops is not None and loops >= int(max_loops):
                out = _write_idle_status(
                    pid=current_pid,
                    cfg=cfg,
                    strategies=strategies,
                    session_strategy_id=session_strategy_id,
                    last_result=last_result,
                )
                out["status"] = "stopped"
                out["reason"] = "max_loops"
                out["loops"] = loops
                out["summary_text"] = "Paper evidence collector daily loop stopped after reaching max_loops."
                _write_status(out)
                return out

            time.sleep(max(1.0, float(poll_interval_sec)))
    finally:
        _clear_pid_state()


def _detached_log_path() -> Path:
    path = runtime_dir() / "logs" / "paper_strategy_evidence.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _start_detached_daily_loop(
    raw_argv: list[str],
    *,
    wait_timeout_sec: float = 5.0,
) -> dict[str, object]:
    existing = load_runtime_status()
    if bool(existing.get("pid_alive")):
        return {
            "ok": True,
            "status": "running",
            "reason": "already_running",
            "pid": int(existing.get("pid") or 0),
            "log_file": str(_detached_log_path()),
        }

    child_argv = [str(item) for item in raw_argv if str(item) != "--detach"]
    command = [sys.executable, str(Path(__file__).resolve()), *child_argv]
    log_path = _detached_log_path()
    kwargs: dict[str, object] = {
        "cwd": str(ROOT),
        "env": dict(os.environ),
        "stdin": subprocess.DEVNULL,
        "stderr": subprocess.STDOUT,
        "close_fds": True,
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

    with log_path.open("a", encoding="utf-8", buffering=1) as log:
        kwargs["stdout"] = log
        proc = subprocess.Popen(command, **kwargs)

    deadline = time.monotonic() + max(0.0, float(wait_timeout_sec))
    while time.monotonic() <= deadline:
        current = load_runtime_status()
        if bool(current.get("pid_alive")) and int(current.get("pid") or 0) == int(proc.pid):
            return {
                "ok": True,
                "status": str(current.get("status") or "running"),
                "reason": "detached_started",
                "pid": int(proc.pid),
                "log_file": str(log_path),
            }
        exit_code = proc.poll()
        if exit_code is not None:
            return {
                "ok": False,
                "status": "failed",
                "reason": "detached_process_exited",
                "pid": int(proc.pid),
                "exit_code": int(exit_code),
                "log_file": str(log_path),
            }
        time.sleep(0.05)

    return {
        "ok": True,
        "status": "starting",
        "reason": "detached_started_waiting_for_status",
        "pid": int(proc.pid),
        "log_file": str(log_path),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Run a managed paper strategy evidence collection campaign.")
    ap.add_argument(
        "--strategies",
        default="ema_cross,breakout_donchian,mean_reversion_rsi",
        help="Comma-separated canonical strategy IDs to run sequentially.",
    )
    ap.add_argument("--runtime-sec", type=float, default=900.0, help="Per-strategy runtime window in seconds")
    ap.add_argument("--strategy-drain-sec", type=float, default=2.0, help="Wait after each strategy stop for fills to settle")
    ap.add_argument("--symbol", default="BTC/USD", help="Runtime symbol for tick publisher, runner, and paper engine")
    ap.add_argument("--venue", default="coinbase", help="Runtime venue for tick publisher, runner, and paper engine")
    ap.add_argument("--tick-interval-sec", type=float, default=2.0, help="Tick publisher interval while the campaign is active")
    ap.add_argument(
        "--strategy-min-bars",
        type=int,
        default=0,
        help="Optional strategy warmup override for managed evidence runs. Uses the greater of this value and the strategy's required history.",
    )
    ap.add_argument(
        "--signal-source",
        default="",
        help="Optional signal source override, e.g. public_ohlcv_1m or public_ohlcv_5m.",
    )
    ap.add_argument(
        "--allow-first-signal-trade",
        action="store_true",
        help="Allow the first actionable signal after warmup to enqueue immediately during managed evidence runs.",
    )
    ap.add_argument("--evidence-symbol", default="", help="Optional symbol override for the synthetic evidence cycle")
    ap.add_argument("--paper-history-path", default="", help="Optional trade_journal.sqlite path override")
    ap.add_argument("--max-strategies", type=int, default=0, help="Optional cap for test/manual runs")
    ap.add_argument("--daily-loop", action="store_true", help="Keep the collector alive and run one campaign per new UTC day")
    ap.add_argument(
        "--detach",
        action="store_true",
        help="Start daily-loop mode as a persistent detached process and return after startup verification",
    )
    ap.add_argument("--poll-interval-sec", type=float, default=300.0, help="Polling interval for daily loop mode")
    ap.add_argument("--max-loops", type=int, default=0, help="Optional loop cap for tests/manual use")
    ap.add_argument("--session-strategy-id", default="", help="Optional evidence strategy ID for session logs")
    ap.add_argument(
        "--no-desktop-notify",
        action="store_true",
        help="Disable local desktop notifications for the managed paper sim monitor.",
    )
    ap.add_argument("--stop", action="store_true", help="Request stop for the active managed campaign")
    ap.add_argument("--status", action="store_true", help="Show managed campaign runtime status")
    args = ap.parse_args()

    if args.detach and (not args.daily_loop or args.stop or args.status):
        ap.error("--detach requires --daily-loop and cannot be combined with --stop or --status")
    if args.stop:
        print(json.dumps(request_stop(), indent=2, default=str))
        return 0
    if args.status:
        print(json.dumps(load_runtime_status(), indent=2, default=str))
        return 0
    if args.detach:
        out = _start_detached_daily_loop(list(sys.argv[1:]))
        print(json.dumps(out, indent=2, default=str))
        return 0 if bool(out.get("ok")) else 1

    strategies = _strategy_items(args.strategies)
    signal_source = _default_signal_source(strategies=strategies, requested=str(args.signal_source or ""))
    cfg = PaperStrategyEvidenceServiceCfg(
        strategies=strategies,
        per_strategy_runtime_sec=float(args.runtime_sec or 900.0),
        strategy_drain_sec=float(args.strategy_drain_sec or 2.0),
        symbol=str(args.symbol or "BTC/USD"),
        venue=str(args.venue or "coinbase"),
        tick_publish_interval_sec=float(args.tick_interval_sec or 2.0),
        strategy_min_bars=int(args.strategy_min_bars or 0),
        signal_source=signal_source,
        allow_first_signal_trade=bool(args.allow_first_signal_trade),
        evidence_symbol=str(args.evidence_symbol or ""),
        paper_history_path=str(args.paper_history_path or ""),
        paper_sim_monitor_desktop_notify=not bool(args.no_desktop_notify),
    )
    max_strategies = int(args.max_strategies) if int(args.max_strategies or 0) > 0 else None
    session_strategy_id = _session_strategy_id(
        strategies=(strategies[:max_strategies] if max_strategies else strategies),
        override=str(args.session_strategy_id or ""),
    )
    if args.daily_loop:
        out = _run_daily_loop(
            cfg,
            max_strategies=max_strategies,
            session_strategy_id=session_strategy_id,
            poll_interval_sec=float(args.poll_interval_sec or 300.0),
            max_loops=(int(args.max_loops) if int(args.max_loops or 0) > 0 else None),
        )
    else:
        out = _run_one_campaign(
            cfg,
            max_strategies=max_strategies,
            session_strategy_id=session_strategy_id,
        )
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
