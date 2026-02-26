from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from services.logging.app_logger import get_logger

def now_ms() -> int:
    return int(time.time() * 1000)

logger = get_logger("services_supervisor")


def _safe_read_yaml(path: Path) -> Dict[str, Any]:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8", errors="replace")) or {}
    except Exception:
        logger.exception("services_supervisor: failed to read config path=%s", path)
        return {}


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        # Works on Unix; on Windows, Python supports os.kill for process existence checks as well.
        os.kill(pid, 0)
        return True
    except Exception:
        return False


@dataclass
class ProcInfo:
    name: str
    popen: subprocess.Popen
    start_ms: int
    restarts: int = 0
    last_exit_code: Optional[int] = None


class SupervisorDaemon:
    def __init__(self, cfg_path: str = "config/services.yaml"):
        self.cfg_path = Path(cfg_path)
        self.root = Path(".").resolve()
        self.data_dir = self.root / "data" / "supervisor"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.pid_path = self.data_dir / "daemon.pid"
        self.stop_path = self.data_dir / "STOP"
        self.status_path = self.data_dir / "status.json"

        self.procs: Dict[str, ProcInfo] = {}

    def write_pid(self) -> None:
        self.pid_path.write_text(str(os.getpid()), encoding="utf-8")

    def clear_stop_flag(self) -> None:
        if self.stop_path.exists():
            self.stop_path.unlink()

    def should_stop(self) -> bool:
        return self.stop_path.exists()

    def load_cfg(self) -> Dict[str, Any]:
        return _safe_read_yaml(self.cfg_path)

    def _env_for(self, service: Dict[str, Any]) -> Dict[str, str]:
        env = dict(os.environ)
        extra = service.get("env") or {}
        if isinstance(extra, dict):
            for k, v in extra.items():
                env[str(k)] = str(v)
        # Ensure unbuffered output for logs
        env.setdefault("PYTHONUNBUFFERED", "1")
        return env

    def start_service(self, name: str, service: Dict[str, Any]) -> None:
        if name in self.procs and self.procs[name].popen.poll() is None:
            return

        cmd = service.get("cmd")
        if not isinstance(cmd, list) or not cmd:
            raise RuntimeError(f"Service {name} missing cmd list")
        cwd = str(service.get("cwd") or str(self.root))
        env = self._env_for(service)

        log_dir = self.data_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"{name}.log"
        log_f = open(log_path, "a", encoding="utf-8", errors="replace")

        p = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdout=log_f,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self.procs[name] = ProcInfo(name=name, popen=p, start_ms=now_ms())
        self._write_status()

    def stop_service(self, name: str, timeout_sec: float = 8.0) -> None:
        pi = self.procs.get(name)
        if not pi:
            return
        p = pi.popen
        if p.poll() is not None:
            return

        try:
            if sys.platform.startswith("win"):
                p.terminate()
            else:
                p.send_signal(signal.SIGTERM)
        except Exception:
            logger.exception("services_supervisor: terminate failed service=%s pid=%s", name, p.pid)

        t0 = time.time()
        while time.time() - t0 < timeout_sec:
            if p.poll() is not None:
                break
            time.sleep(0.1)

        if p.poll() is None:
            try:
                p.kill()
            except Exception:
                logger.exception("services_supervisor: force kill failed service=%s pid=%s", name, p.pid)

        pi.last_exit_code = p.poll()
        self._write_status()

    def stop_all(self) -> None:
        for name in list(self.procs.keys()):
            self.stop_service(name)

    def _write_status(self) -> None:
        status = {
            "ts_ms": now_ms(),
            "daemon_pid": os.getpid(),
            "services": {},
        }
        for name, pi in self.procs.items():
            code = pi.popen.poll()
            status["services"][name] = {
                "pid": pi.popen.pid,
                "running": code is None,
                "start_ms": pi.start_ms,
                "uptime_ms": max(0, now_ms() - pi.start_ms),
                "restarts": pi.restarts,
                "last_exit_code": pi.last_exit_code if code is None else code,
                "log_path": str((self.data_dir / "logs" / f"{name}.log").resolve()),
            }
        self.status_path.write_text(json.dumps(status, indent=2, sort_keys=True), encoding="utf-8")

    def _maybe_restart(self, name: str, service: Dict[str, Any]) -> None:
        pi = self.procs.get(name)
        if not pi:
            return
        code = pi.popen.poll()
        if code is None:
            return
        # restart policy
        if not bool(service.get("auto_restart", True)):
            pi.last_exit_code = code
            return
        # backoff
        backoff_ms = int(service.get("restart_backoff_ms", 1500))
        time.sleep(max(0.0, backoff_ms / 1000.0))
        pi.restarts += 1
        pi.last_exit_code = code
        # Start again (fresh Popen)
        self.start_service(name, service)

    def run(self) -> int:
        self.write_pid()
        self.clear_stop_flag()

        cfg = self.load_cfg()
        services = cfg.get("services") or {}
        if not isinstance(services, dict) or not services:
            raise SystemExit("No services configured in config/services.yaml")

        # Start enabled services
        for name, svc in services.items():
            if bool((svc or {}).get("enabled", True)):
                self.start_service(name, svc)

        # Main loop
        tick_ms = int(cfg.get("tick_ms", 1000))
        while True:
            if self.should_stop():
                break

            # Reload config periodically (supports toggling enabled flags)
            cfg = self.load_cfg()
            services = cfg.get("services") or {}
            for name, svc in services.items():
                if not isinstance(svc, dict):
                    continue
                enabled = bool(svc.get("enabled", True))

                if enabled:
                    # start if missing
                    if name not in self.procs or self.procs[name].popen.poll() is not None:
                        try:
                            self.start_service(name, svc)
                        except Exception:
                            logger.exception("services_supervisor: start failed service=%s", name)
                    # restart if crashed
                    try:
                        self._maybe_restart(name, svc)
                    except Exception:
                        logger.exception("services_supervisor: restart check failed service=%s", name)
                else:
                    # stop if running
                    try:
                        self.stop_service(name)
                    except Exception:
                        logger.exception("services_supervisor: stop failed service=%s", name)

            self._write_status()
            time.sleep(max(0.05, tick_ms / 1000.0))

        # Shutdown
        self.stop_all()
        self._write_status()
        return 0


def main() -> int:
    cfg_path = os.environ.get("SERVICES_CONFIG", "config/services.yaml")
    d = SupervisorDaemon(cfg_path=cfg_path)
    return d.run()


if __name__ == "__main__":
    raise SystemExit(main())
