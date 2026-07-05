from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

import services.execution.strategy_runner as runner


@pytest.fixture()
def lock_env(tmp_path, monkeypatch):
    locks_dir = tmp_path / "locks"
    lock_file = locks_dir / "strategy_runner.lock"
    monkeypatch.setattr(runner, "LOCKS", locks_dir)
    monkeypatch.setattr(runner, "LOCK_FILE", lock_file)
    return lock_file


def _dead_pid() -> int:
    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    proc.wait(timeout=10)
    return proc.pid


def test_acquire_then_second_acquire_fails_while_holder_alive(lock_env):
    assert runner._acquire_lock() is True
    payload = json.loads(lock_env.read_text(encoding="utf-8"))
    assert payload["pid"] == os.getpid()
    assert runner._acquire_lock() is False


def test_release_then_reacquire(lock_env):
    assert runner._acquire_lock() is True
    runner._release_lock()
    assert not lock_env.exists()
    assert runner._acquire_lock() is True


def test_stale_dead_pid_lock_is_reclaimed(lock_env):
    lock_env.parent.mkdir(parents=True, exist_ok=True)
    lock_env.write_text(
        json.dumps({"pid": _dead_pid(), "ts": "2026-01-01T00:00:00+00:00"}) + "\n",
        encoding="utf-8",
    )
    assert runner._acquire_lock() is True
    payload = json.loads(lock_env.read_text(encoding="utf-8"))
    assert payload["pid"] == os.getpid()


def test_live_pid_lock_is_not_stolen(lock_env):
    lock_env.parent.mkdir(parents=True, exist_ok=True)
    lock_env.write_text(
        json.dumps({"pid": os.getpid(), "ts": "2026-01-01T00:00:00+00:00"}) + "\n",
        encoding="utf-8",
    )
    assert runner._acquire_lock() is False


def test_malformed_lock_file_fails_closed(lock_env):
    lock_env.parent.mkdir(parents=True, exist_ok=True)
    lock_env.write_text("not-json\n", encoding="utf-8")
    assert runner._acquire_lock() is False
    assert lock_env.read_text(encoding="utf-8") == "not-json\n"


def test_acquisition_is_atomic_no_check_then_write_window(lock_env, monkeypatch):
    real_open = os.open
    created_by_racer = {}

    def racing_open(path, flags, *args, **kwargs):
        if str(path) == str(lock_env) and not created_by_racer:
            lock_env.parent.mkdir(parents=True, exist_ok=True)
            lock_env.write_text(
                json.dumps({"pid": os.getpid(), "ts": "race"}) + "\n",
                encoding="utf-8",
            )
            created_by_racer["done"] = True
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", racing_open)
    assert runner._acquire_lock() is False
