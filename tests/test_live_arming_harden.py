from __future__ import annotations

import json
import time
from pathlib import Path


def _write_arming_file(path: Path, *, armed: bool, ts_epoch: float | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "version": 1,
        "armed": {
            "armed": armed,
            "writer": "test",
            "reason": "test",
            "ts_epoch": ts_epoch if ts_epoch is not None else time.time(),
        },
        "active": None,
    }), encoding="utf-8")


def _clear_env(monkeypatch):
    monkeypatch.delenv("CBP_EXECUTION_ARMED", raising=False)
    monkeypatch.delenv("CBP_LIVE_ENABLED", raising=False)
    monkeypatch.delenv("CBP_EXECUTION_LIVE_ENABLED", raising=False)


def test_env_truthy_arms_regardless_of_persisted(monkeypatch, tmp_path):
    import services.execution.live_arming as la
    path = tmp_path / "live_arming.json"
    _write_arming_file(path, armed=False)
    monkeypatch.setattr(la, "STATE_PATH", path)
    _clear_env(monkeypatch)
    monkeypatch.setenv("CBP_EXECUTION_ARMED", "1")
    armed, reason = la.live_armed_signal()
    assert armed is True
    assert "env:CBP_EXECUTION_ARMED" in reason


def test_env_explicit_false_blocks_persisted_armed(monkeypatch, tmp_path):
    import services.execution.live_arming as la
    path = tmp_path / "live_arming.json"
    _write_arming_file(path, armed=True)
    monkeypatch.setattr(la, "STATE_PATH", path)
    _clear_env(monkeypatch)
    monkeypatch.setenv("CBP_EXECUTION_ARMED", "0")
    armed, reason = la.live_armed_signal()
    assert armed is False
    assert "env_false" in reason


def test_no_env_persisted_armed_fresh_returns_armed(monkeypatch, tmp_path):
    import services.execution.live_arming as la
    path = tmp_path / "live_arming.json"
    _write_arming_file(path, armed=True, ts_epoch=time.time())
    monkeypatch.setattr(la, "STATE_PATH", path)
    _clear_env(monkeypatch)
    monkeypatch.setenv("CBP_LIVE_ARMING_MAX_AGE_S", "300")
    armed, reason = la.live_armed_signal()
    assert armed is True
    assert "persisted:live_arming.json" in reason


def test_no_env_persisted_armed_stale_returns_not_armed(monkeypatch, tmp_path):
    import services.execution.live_arming as la
    path = tmp_path / "live_arming.json"
    _write_arming_file(path, armed=True, ts_epoch=time.time() - 999)
    monkeypatch.setattr(la, "STATE_PATH", path)
    _clear_env(monkeypatch)
    monkeypatch.setenv("CBP_LIVE_ARMING_MAX_AGE_S", "300")
    armed, reason = la.live_armed_signal()
    assert armed is False
    assert "persisted_stale" in reason


def test_corrupt_arming_file_returns_persisted_error(monkeypatch, tmp_path):
    import services.execution.live_arming as la
    path = tmp_path / "live_arming.json"
    path.write_text("{invalid json!!!", encoding="utf-8")
    monkeypatch.setattr(la, "STATE_PATH", path)
    _clear_env(monkeypatch)
    armed, reason = la.live_armed_signal()
    assert armed is False
    assert "persisted_error" in reason


def test_empty_arming_file_returns_persisted_error(monkeypatch, tmp_path):
    import services.execution.live_arming as la
    path = tmp_path / "live_arming.json"
    path.write_bytes(b"")
    monkeypatch.setattr(la, "STATE_PATH", path)
    _clear_env(monkeypatch)
    armed, reason = la.live_armed_signal()
    assert armed is False
    assert "persisted_error" in reason


def test_absent_arming_file_returns_not_armed(monkeypatch, tmp_path):
    import services.execution.live_arming as la
    path = tmp_path / "live_arming.json"
    monkeypatch.setattr(la, "STATE_PATH", path)
    _clear_env(monkeypatch)
    armed, reason = la.live_armed_signal()
    assert armed is False
    assert "persisted_error" not in reason


def test_arming_ttl_boundary(monkeypatch, tmp_path):
    import services.execution.live_arming as la
    path = tmp_path / "live_arming.json"
    monkeypatch.setattr(la, "STATE_PATH", path)
    _clear_env(monkeypatch)
    monkeypatch.setenv("CBP_LIVE_ARMING_MAX_AGE_S", "60")

    _write_arming_file(path, armed=True, ts_epoch=time.time() - 61)
    armed, reason = la.live_armed_signal()
    assert armed is False
    assert "persisted_stale" in reason

    _write_arming_file(path, armed=True, ts_epoch=time.time() - 59)
    armed, reason = la.live_armed_signal()
    assert armed is True
    assert "persisted:live_arming.json" in reason
