"""tests/test_managed_component.py

Tests for services/control/managed_component.py
"""
from __future__ import annotations

import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))


def _make_component(tmp_path, name="test_svc"):
    from services.control.managed_component import ManagedComponent
    lock_dir   = tmp_path / "locks"
    status_dir = tmp_path / "snapshots"
    flags_dir  = tmp_path / "flags"
    for d in [lock_dir, status_dir, flags_dir]:
        d.mkdir(parents=True, exist_ok=True)
    return ManagedComponent(name, lock_dir=lock_dir, status_dir=status_dir, flags_dir=flags_dir)


class TestManagedComponentState:
    def test_no_lock_is_not_alive(self, tmp_path):
        mc = _make_component(tmp_path)
        assert mc.is_alive() is False

    def test_no_lock_is_not_stale(self, tmp_path):
        mc = _make_component(tmp_path)
        assert mc.is_stale() is False

    def test_lock_with_dead_pid_is_stale(self, tmp_path):
        mc = _make_component(tmp_path)
        mc.lock_file.write_text(json.dumps({"pid": 9999999}))
        with patch("services.control.managed_component._process_alive", return_value=False):
            assert mc.is_stale() is True
            assert mc.is_alive() is False

    def test_lock_with_live_pid_is_alive(self, tmp_path):
        mc = _make_component(tmp_path)
        mc.lock_file.write_text(json.dumps({"pid": os.getpid()}))
        assert mc.is_alive() is True
        assert mc.is_stale() is False

    def test_pid_returns_none_when_no_lock(self, tmp_path):
        mc = _make_component(tmp_path)
        assert mc.pid() is None

    def test_pid_returns_value_from_lock(self, tmp_path):
        mc = _make_component(tmp_path)
        mc.lock_file.write_text(json.dumps({"pid": 12345}))
        assert mc.pid() == 12345

    def test_status_dict_has_required_keys(self, tmp_path):
        mc = _make_component(tmp_path)
        s = mc.status()
        assert "name" in s
        assert "has_lock" in s
        assert "pid_alive" in s
        assert "stale" in s

    def test_status_reads_status_file(self, tmp_path):
        mc = _make_component(tmp_path)
        mc.status_file.write_text(json.dumps({"status": "running", "pid": 1}))
        s = mc.status()
        assert s["status"] == "running"


class TestManagedComponentLifecycle:
    def test_clean_stale_lock_removes_file(self, tmp_path):
        mc = _make_component(tmp_path)
        mc.lock_file.write_text(json.dumps({"pid": 9999999}))
        with patch("services.control.managed_component._process_alive", return_value=False):
            result = mc.clean_stale_lock()
        assert result is True
        assert not mc.lock_file.exists()

    def test_clean_stale_lock_no_op_if_alive(self, tmp_path):
        mc = _make_component(tmp_path)
        mc.lock_file.write_text(json.dumps({"pid": os.getpid()}))
        result = mc.clean_stale_lock()
        assert result is False
        assert mc.lock_file.exists()

    def test_stop_writes_flag_file(self, tmp_path):
        mc = _make_component(tmp_path)
        mc.stop()
        assert mc.stop_flag.exists()
        assert mc.stop_flag.read_text().strip() == "stop"

    def test_clear_stop_flag_removes_file(self, tmp_path):
        mc = _make_component(tmp_path)
        mc.stop()
        assert mc.stop_flag.exists()
        mc.clear_stop_flag()
        assert not mc.stop_flag.exists()

    def test_wait_stopped_returns_true_when_not_alive(self, tmp_path):
        mc = _make_component(tmp_path)
        # No lock file → not alive → should return immediately
        result = mc.wait_stopped(timeout_sec=1.0)
        assert result is True

    def test_wait_stopped_returns_false_on_timeout(self, tmp_path):
        mc = _make_component(tmp_path)
        mc.lock_file.write_text(json.dumps({"pid": os.getpid()}))
        result = mc.wait_stopped(timeout_sec=0.3)
        assert result is False  # still "alive" (our own PID)

    def test_no_lock_file_pid_returns_none(self, tmp_path):
        mc = _make_component(tmp_path)
        assert mc.pid() is None
        assert mc.is_alive() is False
