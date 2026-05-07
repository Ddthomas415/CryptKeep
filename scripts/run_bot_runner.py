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
import signal
import threading
import time
from typing import Any, Dict

from services.config_loader import load_runtime_trading_config
from services.os.app_paths import runtime_dir
from services.runtime.process_supervisor import (
    is_running,
    request_system_guard_halt,
    start_process,
    status,
    stop_process,
)

MANAGED_SERVICES = (
    "pipeline",
    "executor",
    "intent_consumer",
    "ops_signal_adapter",
    "ops_risk_gate",
    "reconciler",
)
STATUS_PATH = runtime_dir() / "flags" / "bot_runner.status.json"
STOP_EVENT = threading.Event()


def _normalize_symbol(sym: str) -> str:
    return str(sym).strip().upper().replace("-", "/")


def _normalize_symbols(value: Any) -> list[str]:
    if isinstance(value, str):
        parts = [x.strip() for x in value.split(",") if x.strip()]
    elif isinstance(value, list):
        parts = [str(x).strip() for x in value if str(x).strip()]
    else:
        parts = []
    out = [_normalize_symbol(x) for x in parts]
    return out


def load_trading_cfg(path: str = "config/trading.yaml") -> dict[str, Any]:
    return load_runtime_trading_config(path)


def _paper_venue(cfg: dict[str, Any], execution: dict[str, Any]) -> str:
    pipeline = cfg.get("pipeline") if isinstance(cfg.get("pipeline"), dict) else {}
    execution_venue = str(execution.get("venue") or "").strip().lower()
    pipeline_venue = str(pipeline.get("exchange_id") or "").strip().lower()
    root_venue = str(cfg.get("venue") or "").strip().lower()

    candidates = [v for v in (execution_venue, pipeline_venue, root_venue) if v]
    if not candidates:
        raise RuntimeError("CBP_CONFIG_REQUIRED:missing_config:pipeline.exchange_id")

    explicit = {v for v in (execution_venue, pipeline_venue) if v}
    if len(explicit) > 1:
        raise RuntimeError("CBP_CONFIG_REQUIRED:conflicting_config:execution.venue_vs_pipeline.exchange_id")

    return execution_venue or pipeline_venue or root_venue


def desired_state(cfg: dict[str, Any]) -> dict[str, Any]:
    execution = cfg.get("execution") if isinstance(cfg.get("execution"), dict) else {}
    mode = str(cfg.get("mode") or "").strip().lower()
    if not mode:
        mode = str(execution.get("executor_mode") or "").strip().lower()
    if mode not in {"paper", "live"}:
        raise RuntimeError("CBP_CONFIG_REQUIRED:missing_or_invalid_config:execution.executor_mode")

    live = cfg.get("live") if isinstance(cfg.get("live"), dict) else {}
    live_enabled = bool(execution.get("live_enabled", live.get("enabled", False)))
    if mode == "paper" and not live_enabled:
        venue = _paper_venue(cfg, execution)
    else:
        venue = str(live.get("exchange_id") or cfg.get("venue") or "").strip().lower()
        if not venue:
            raise RuntimeError("CBP_CONFIG_REQUIRED:missing_config:live.exchange_id")
    symbols = _normalize_symbols(cfg.get("symbols"))
    if not symbols:
        raise RuntimeError(r"CBP_CONFIG_REQUIRED:missing_config:symbols[0]")
    with_reconcile = mode == "live" or live_enabled
    return {
        "mode": mode,
        "live_enabled": live_enabled,
        "venue": venue,
        "symbols": symbols,
        "with_reconcile": with_reconcile,
    }


def desired_services(state: dict[str, Any]) -> list[str]:
    names = ["pipeline", "ops_signal_adapter", "ops_risk_gate"]
    if state.get("mode") == "live" or state.get("live_enabled"):
        names.append("intent_consumer")
    else:
        names.append("executor")
    if bool(state.get("with_reconcile")):
        names.append("reconciler")
    return names


def command_map() -> dict[str, list[str]]:
    py = sys.executable
    return {
        "pipeline": [py, "scripts/run_pipeline_safe.py"],
        "executor": [py, "scripts/run_intent_executor_safe.py"],
        "intent_consumer": [py, "scripts/run_intent_consumer_safe.py", "run"],
        "ops_signal_adapter": [py, "scripts/run_ops_signal_adapter.py", "run"],
        "ops_risk_gate": [py, "scripts/run_ops_risk_gate_service.py", "run"],
        "reconciler": [py, "scripts/run_live_reconciler_safe.py", "run"],
    }


def state_signature(state: dict[str, Any]) -> str:
    payload = {
        "mode": state.get("mode"),
        "live_enabled": bool(state.get("live_enabled")),
        "venue": state.get("venue"),
        "symbols": list(state.get("symbols") or []),
        "with_reconcile": bool(state.get("with_reconcile")),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def apply_state(state: dict[str, Any], *, force_restart: bool = False) -> dict[str, Any]:
    wanted = desired_services(state)
    cmds = command_map()

    stopped: list[dict[str, Any]] = []
    started: list[dict[str, Any]] = []

    if force_restart:
        # Hot-reload path: restart only services that should be active.
        for name in wanted:
            if is_running(name):
                stopped.append(stop_process(name))
        for name in wanted:
            started.append(start_process(name, cmds[name]))
    else:
        # Converge path: stop no-longer-wanted services; ensure wanted services are running.
        for name in MANAGED_SERVICES:
            if name not in wanted and is_running(name):
                stopped.append(stop_process(name))
        for name in wanted:
            started.append(start_process(name, cmds[name]))

    return {
        "ok": True,
        "force_restart": bool(force_restart),
        "wanted": wanted,
        "started": started,
        "stopped": stopped,
        "status": status(list(MANAGED_SERVICES)),
    }


def write_status(payload: dict[str, Any]) -> None:
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _handle_signal(signum: int, _frame) -> None:
    STOP_EVENT.set()
    write_status({"ok": True, "status": "stopping", "signal": int(signum), "ts_epoch": time.time()})


def _install_signal_handlers() -> None:
    for sig_name in ("SIGTERM", "SIGINT"):
        sig = getattr(signal, sig_name, None)
        if sig is None:
            continue
        try:
            signal.signal(sig, _handle_signal)
        except Exception:
            continue


def _shutdown_managed_services() -> int:
    # On shutdown, raise shared halt state before tearing down managed services.
    system_guard = request_system_guard_halt(writer="bot_runner", reason="bot_runner_shutdown")
    shutdown = []
    for name in MANAGED_SERVICES:
        if is_running(name):
            shutdown.append(stop_process(name))
    write_status(
        {
            "ok": bool(system_guard.get("ok")),
            "status": "stopped",
            "system_guard": system_guard,
            "stopped": shutdown,
            "ts_epoch": time.time(),
        }
    )
    return 0


def run_loop(*, cfg_path: str = "config/trading.yaml", interval_sec: float = 2.0, once: bool = False) -> int:
    STOP_EVENT.clear()
    _install_signal_handlers()
    last_sig: str | None = None

    while not STOP_EVENT.is_set():
        cfg = load_trading_cfg(cfg_path)
        try:
            state = desired_state(cfg)
        except RuntimeError as exc:
            payload = {
                "ok": False,
                "status": "blocked",
                "error": str(exc),
                "cfg_path": str(cfg_path),
                "ts_epoch": time.time(),
            }
            write_status(payload)
            print(payload)
            return 2
        sig = state_signature(state)

        force_restart = last_sig is not None and sig != last_sig
        result = apply_state(state, force_restart=force_restart)
        result.update(
            {
                "ok": True,
                "status": "running",
                "hot_reloaded": bool(force_restart),
                "state": state,
                "signature": sig,
                "ts_epoch": time.time(),
            }
        )
        write_status(result)
        print(result)
        last_sig = sig

        if once:
            one_shot = dict(result)
            one_shot["status"] = "converged"
            one_shot["one_shot"] = True
            one_shot["ts_epoch"] = time.time()
            write_status(one_shot)
            return 0
        if STOP_EVENT.wait(max(0.1, float(interval_sec))):
            break

    return _shutdown_managed_services()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/trading.yaml")
    ap.add_argument("--interval", type=float, default=2.0)
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()
    return run_loop(cfg_path=str(args.config), interval_sec=float(args.interval), once=bool(args.once))


if __name__ == "__main__":
    raise SystemExit(main())
