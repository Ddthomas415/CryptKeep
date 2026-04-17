"""services/analytics/paper_campaign_lifecycle.py

Process lifecycle management for the paper campaign.

Extracted from paper_strategy_evidence_service.py to reduce coupling.
Owns: component start/stop/wait, runtime file paths, stale lock cleanup.

Called by: paper_strategy_evidence_service.run_campaign()
"""
from __future__ import annotations

import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from services.os.app_paths import runtime_dir
from services.logging.app_logger import get_logger

_LOG = get_logger("analytics.paper_campaign_lifecycle")


def get_component_paths(name: str) -> dict[str, Path]:
    """Return canonical file paths for a managed component."""
    _PATHS = {
        "tick_publisher": {
            "lock_file":   runtime_dir() / "locks" / "tick_publisher.lock",
            "status_file": runtime_dir() / "snapshots" / "system_status.latest.json",
            "stop_flag":   runtime_dir() / "flags" / "tick_publisher.stop",
        },
        "paper_engine": {
            "lock_file":   runtime_dir() / "locks" / "paper_engine.lock",
            "status_file": runtime_dir() / "flags" / "paper_engine.status.json",
            "stop_flag":   runtime_dir() / "flags" / "paper_engine.stop",
        },
        "strategy_runner": {
            "lock_file":   runtime_dir() / "locks" / "strategy_runner.lock",
            "status_file": runtime_dir() / "flags" / "strategy_runner.status.json",
            "stop_flag":   runtime_dir() / "flags" / "strategy_runner.stop",
        },
    }
    return _PATHS.get(name, {})


def component_is_alive(name: str) -> bool:
    """Return True if the named component has a live PID."""
    paths = get_component_paths(name)
    lock = paths.get("lock_file")
    if not lock or not lock.exists():
        return False
    try:
        import json
        payload = json.loads(lock.read_text(encoding="utf-8"))
        pid = int(payload.get("pid") or 0)
        if pid <= 0:
            return False
        # Check if PID is alive
        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, PermissionError):
            return False
    except Exception:
        return False


def clean_stale_lock(name: str) -> bool:
    """Remove lock file if PID is dead. Returns True if cleaned."""
    paths = get_component_paths(name)
    lock = paths.get("lock_file")
    if not lock or not lock.exists():
        return False
    if not component_is_alive(name):
        try:
            lock.unlink(missing_ok=True)
            _LOG.info("stale_lock_cleaned component=%s", name)
            return True
        except Exception as _err:
            _LOG.warning("stale_lock_clean_failed component=%s err=%s", name, _err)
    return False


def stop_component(name: str) -> None:
    """Write stop flag for a component."""
    paths = get_component_paths(name)
    stop = paths.get("stop_flag")
    if stop:
        stop.parent.mkdir(parents=True, exist_ok=True)
        stop.write_text("stop\n", encoding="utf-8")
        _LOG.info("stop_flag_written component=%s", name)


def wait_stopped(name: str, timeout_sec: float = 10.0) -> bool:
    """Wait until component is no longer alive. Returns True if stopped."""
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        if not component_is_alive(name):
            return True
        time.sleep(0.2)
    return False


def teardown_all(components: tuple[str, ...] = ("strategy_runner", "paper_engine", "tick_publisher"),
                 timeouts: dict[str, float] | None = None) -> dict[str, Any]:
    """Stop all components in order. Returns {clean: bool, still_alive: list}."""
    _timeouts = timeouts or {"strategy_runner": 8.0, "paper_engine": 8.0, "tick_publisher": 10.0}
    still_alive = []

    for name in components:
        if component_is_alive(name):
            _LOG.info("teardown stopping %s", name)
            stop_component(name)
            stopped = wait_stopped(name, timeout_sec=_timeouts.get(name, 8.0))
            if stopped:
                _LOG.info("teardown %s stopped cleanly", name)
            else:
                _LOG.error("teardown %s still alive after timeout — run make paper-stop", name)
                still_alive.append(name)
        else:
            _LOG.info("teardown %s already stopped", name)

    return {"clean": len(still_alive) == 0, "still_alive": still_alive}
