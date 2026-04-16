"""services/control/managed_component.py

Shared managed-component lifecycle utility.

Eliminates the duplicated lock/status/stop/stale-lock pattern that exists
across tick_publisher, paper_engine, and strategy_runner. Every managed
component in the paper campaign follows the same contract:

  start  → writes PID to lock file, writes status file
  stop   → writes stop flag file; process reads and exits
  status → reads lock + status files, validates PID alive
  clean  → removes stale lock if PID is dead

Usage:
    from services.control.managed_component import ManagedComponent

    tick = ManagedComponent("tick_publisher")
    if tick.is_stale():
        tick.clean_stale_lock()
    if not tick.is_alive():
        tick.start("scripts/run_tick_publisher.py", env={...})
    tick.stop()
    tick.wait_stopped(timeout_sec=10.0)
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from services.os.app_paths import runtime_dir
from services.logging.app_logger import get_logger

_LOG = get_logger("managed_component")


def _process_alive(pid: int) -> bool:
    """Return True if a process with the given PID is running."""
    try:
        os.kill(int(pid), 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists but we can't signal — treat as alive
    except Exception:
        return False


class ManagedComponent:
    """Lifecycle manager for a single named background process.

    Attributes:
        name:        component name (e.g. "tick_publisher")
        lock_file:   path to PID lock file
        status_file: path to JSON status snapshot
        stop_flag:   path to stop-request flag file
    """

    def __init__(
        self,
        name: str,
        *,
        lock_dir: Path | None = None,
        status_dir: Path | None = None,
        flags_dir: Path | None = None,
    ) -> None:
        self.name = name
        base = runtime_dir()
        self.lock_file   = (lock_dir   or base / "locks")   / f"{name}.lock"
        self.status_file = (status_dir or base / "snapshots") / f"{name}.status.json"
        self.stop_flag   = (flags_dir  or base / "flags")   / f"{name}.stop"

    # ------------------------------------------------------------------
    # State queries
    # ------------------------------------------------------------------

    def _read_lock(self) -> dict:
        if not self.lock_file.exists():
            return {}
        try:
            return json.loads(self.lock_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def pid(self) -> int | None:
        lock = self._read_lock()
        try:
            p = int(lock.get("pid") or 0)
            return p if p > 0 else None
        except (ValueError, TypeError):
            return None

    def is_alive(self) -> bool:
        """Return True if the lock file exists AND the PID is running."""
        p = self.pid()
        return p is not None and _process_alive(p)

    def is_stale(self) -> bool:
        """Return True if a lock file exists but the PID is dead."""
        return self.lock_file.exists() and not self.is_alive()

    def status(self) -> dict[str, Any]:
        """Return a structured status dict."""
        p = self.pid()
        alive = _process_alive(p) if p else False
        state: dict[str, Any] = {
            "name":      self.name,
            "has_lock":  self.lock_file.exists(),
            "pid":       p,
            "pid_alive": alive,
            "stale":     self.lock_file.exists() and not alive,
        }
        if self.status_file.exists():
            try:
                payload = json.loads(self.status_file.read_text(encoding="utf-8"))
                state["status"] = payload.get("status", "unknown")
                state["status_payload"] = payload
            except Exception:
                state["status"] = "status_read_error"
        else:
            state["status"] = "no_status_file"
        return state

    # ------------------------------------------------------------------
    # Lifecycle operations
    # ------------------------------------------------------------------

    def clean_stale_lock(self) -> bool:
        """Remove lock file if PID is dead. Returns True if cleaned."""
        if not self.is_stale():
            return False
        try:
            self.lock_file.unlink(missing_ok=True)
            _LOG.info("managed_component.stale_lock_removed component=%s lock=%s",
                      self.name, self.lock_file)
            return True
        except Exception as e:
            _LOG.warning("managed_component.stale_lock_remove_failed component=%s err=%s",
                         self.name, e)
            return False

    def start(
        self,
        script: str,
        *,
        env: dict[str, str] | None = None,
        timeout_sec: float = 5.0,
        cwd: str | None = None,
    ) -> subprocess.Popen:
        """Start the component process.

        Cleans stale lock first. Raises RuntimeError if it fails to start.
        """
        self.clean_stale_lock()

        merged_env = dict(os.environ)
        if env:
            merged_env.update(env)

        proc = subprocess.Popen(
            [merged_env.get("PYTHON", "python3"), script],
            env=merged_env,
            cwd=cwd or str(Path(script).parent.parent),
        )

        deadline = time.monotonic() + timeout_sec
        while time.monotonic() < deadline:
            if self.is_alive() or proc.poll() is not None:
                break
            time.sleep(0.15)

        if not self.is_alive():
            rc = proc.poll()
            raise RuntimeError(
                f"{self.name}_failed_to_start (rc={rc}, lock={self.lock_file.exists()})"
            )

        _LOG.info("managed_component.started component=%s pid=%s", self.name, proc.pid)
        return proc

    def stop(self) -> None:
        """Write stop flag file. The process is expected to read and exit."""
        self.stop_flag.parent.mkdir(parents=True, exist_ok=True)
        self.stop_flag.write_text("stop\n", encoding="utf-8")
        _LOG.info("managed_component.stop_requested component=%s", self.name)

    def wait_stopped(self, timeout_sec: float = 10.0) -> bool:
        """Wait until the component is no longer alive. Returns True if stopped."""
        deadline = time.monotonic() + timeout_sec
        while time.monotonic() < deadline:
            if not self.is_alive():
                return True
            time.sleep(0.2)
        _LOG.warning("managed_component.stop_timeout component=%s timeout=%s",
                     self.name, timeout_sec)
        return False

    def clear_stop_flag(self) -> None:
        """Remove the stop flag file (before restarting a stopped component)."""
        self.stop_flag.unlink(missing_ok=True)
