from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from services.os.app_paths import runtime_dir, ensure_dirs

REPO = Path(__file__).resolve().parents[2]


def _runtime_paths() -> tuple[Path, Path, Path, Path]:
    ensure_dirs()
    rt = runtime_dir()
    flags = rt / "flags"
    logs = rt / "logs"
    locks = rt / "locks"
    pids = rt / "pids"
    for d in (flags, logs, locks, pids):
        d.mkdir(parents=True, exist_ok=True)
    return flags, logs, locks, pids

@dataclass(frozen=True)
class ServiceSpec:
    name: str
    cmd: list[str]
    log_file: Path

def specs_default() -> list[ServiceSpec]:
    _, logs, _, _ = _runtime_paths()
    py = sys.executable
    return [
        ServiceSpec("market_ws",        [py, "-u", str(REPO / "scripts" / "run_ws_ticker_feed_safe.py"), "run"], logs / "market_ws.log"),
        ServiceSpec("tick_publisher",   [py, "-u", str(REPO / "scripts" / "run_tick_publisher.py")],   logs / "tick_publisher.log"),
        ServiceSpec("intent_consumer",  [py, "-u", str(REPO / "scripts" / "run_intent_consumer_safe.py"), "run"],  logs / "intent_consumer.log"),
        ServiceSpec("reconciler",      [py, "-u", str(REPO / "scripts" / "run_live_reconciler_safe.py"), "run"], logs / "reconciler.log"),
        ServiceSpec("ops_signal_adapter",[py, "-u", str(REPO / "scripts" / "run_ops_signal_adapter.py"), "run"], logs / "ops_signal_adapter.log"),
        ServiceSpec("ops_risk_gate",    [py, "-u", str(REPO / "scripts" / "run_ops_risk_gate_service.py"), "run"], logs / "ops_risk_gate.log"),
    ]

def _pid_path(name: str) -> Path:
    _, _, _, pids = _runtime_paths()
    return pids / f"{name}.pid"

def _read_pid(name: str) -> int | None:
    p = _pid_path(name)
    if not p.exists():
        return None
    try:
        return int(p.read_text().strip())
    except Exception:
        return None

def _proc_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False

def is_running(name: str) -> bool:
    pid = _read_pid(name)
    return bool(pid and _proc_alive(pid))

def start_service(spec: ServiceSpec) -> dict:
    if is_running(spec.name):
        return {"ok": True, "name": spec.name, "running": True, "msg": "already running"}

    spec.log_file.parent.mkdir(parents=True, exist_ok=True)
    log = open(spec.log_file, "a", buffering=1)

    env = os.environ.copy()
    # make imports deterministic in child processes
    env["PYTHONPATH"] = str(REPO) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env.setdefault("CBP_STATE_DIR", str(runtime_dir().parent))

    p = subprocess.Popen(
        spec.cmd,
        cwd=str(REPO),
        stdout=log,
        stderr=log,
        env=env,
        start_new_session=True,
        close_fds=True,
    )
    _pid_path(spec.name).write_text(str(p.pid))
    return {"ok": True, "name": spec.name, "running": True, "pid": p.pid}

def stop_service(name: str, hard: bool = False, timeout_s: float = 3.0) -> dict:
    pid = _read_pid(name)
    if not pid or not _proc_alive(pid):
        _pid_path(name).unlink(missing_ok=True)
        return {"ok": True, "name": name, "running": False, "msg": "not running"}

    sig = signal.SIGKILL if hard else signal.SIGTERM
    try:
        os.kill(pid, sig)
    except Exception as e:
        _pid_path(name).unlink(missing_ok=True)
        return {"ok": False, "name": name, "error": str(e)}

    if not hard:
        t0 = time.time()
        while time.time() - t0 < timeout_s:
            if not _proc_alive(pid):
                break
            time.sleep(0.05)
        if _proc_alive(pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except Exception:
                pass

    _pid_path(name).unlink(missing_ok=True)
    return {"ok": True, "name": name, "running": False}

def status_service(name: str) -> dict:
    pid = _read_pid(name)
    running = bool(pid and _proc_alive(pid))
    return {"ok": True, "name": name, "running": running, "pid": pid if running else None}

def restart_service(spec: ServiceSpec) -> dict:
    stop_service(spec.name, hard=False)
    return start_service(spec)

def list_services(specs: Iterable[ServiceSpec]) -> list[str]:
    return [s.name for s in specs]

def tail_log(name: str, lines: int = 80) -> str:
    _, logs, _, _ = _runtime_paths()
    path = logs / f"{name}.log"
    if not path.exists():
        return ""
    data = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(data[-max(1, int(lines)):])
