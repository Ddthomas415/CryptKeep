"""
tests/test_live_arming_harden.py

Tests for live_armed_signal() hardening in services/execution/live_arming.py.

Confirmed from file read (audit/risk-p0-v2-review):
  - live_armed_signal() precedence: env truthy -> env explicit false ->
    persisted fresh -> persisted stale -> persisted error
  - TTL env: CBP_LIVE_ARMING_MAX_AGE_S (default 300s)
  - STATE_PATH module-level: monkeypatch.setattr(la, "STATE_PATH", path)
  - Patch fix: get_live_armed_state() now raises on corrupt/unreadable file
    instead of swallowing via _load(), so live_armed_signal() correctly
    returns False, "persisted_error:<type>"
"""
from __future__ import annotations

import json
import time
from pathlib import Path


def _write_arming_file(path: Path, *, armed: bool, ts_epoch: float | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "armed": {
            "armed": armed,
            "writer": "test",
            "reason": "test",
            "ts_epoch": ts_epoch if ts_epoch is not None else time.time(),
        },
        "active": None,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


# ── Test 1 ────────────────────────────────────────────────────────────────

def test_env_truthy_arms_regardless_of_persisted(monkeypatch, tmp_path):
    """env CBP_EXECUTION_ARMED=1 -> armed=True; persisted false is ignored."""
    import services.execution.live_arming as la

    arming_file = tmp_path / "live_arming.json"
    _write_arming_file(arming_file, armed=False)
    monkeypatch.setattr(la, "STATE_PATH", arming_file)
    monkeypatch.setenv("CBP_EXECUTION_ARMED", "1")
    monkeypatch.delenv("CBP_LIVE_ENABLED", raising=False)
    monkeypatch.delenv("CBP_EXECUTION_LIVE_ENABLED", raising=False)

    armed, reason = la.live_armed_signal()

    assert armed is True, f"Expected armed=True, got {armed!r}"
    assert "env:CBP_EXECUTION_ARMED" in reason, f"Expected env source in reason, got {reason!r}"


# ── Test 2 ────────────────────────────────────────────────────────────────

def test_env_explicit_false_blocks_persisted_armed(monkeypatch, tmp_path):
    """env CBP_EXECUTION_ARMED=0 -> armed=False; persisted armed=True cannot override."""
    import services.execution.live_arming as la

    arming_file = tmp_path / "live_arming.json"
    _write_arming_file(arming_file, armed=True, ts_epoch=time.time())
    monkeypatch.setattr(la, "STATE_PATH", arming_file)
    monkeypatch.setenv("CBP_EXECUTION_ARMED", "0")
    monkeypatch.delenv("CBP_LIVE_ENABLED", raising=False)
    monkeypatch.delenv("CBP_EXECUTION_LIVE_ENABLED", raising=False)

    armed, reason = la.live_armed_signal()

    assert armed is False, f"Expected armed=False for explicit env false, got {armed!r}"
    assert "env_false" in reason, f"Expected env_false in reason, got {reason!r}"


# ── Test 3 ────────────────────────────────────────────────────────────────

def test_no_env_persisted_armed_fresh_returns_armed(monkeypatch, tmp_path):
    """No env vars; persisted armed=True with fresh ts -> armed=True."""
    import services.execution.live_arming as la

    arming_file = tmp_path / "live_arming.json"
    _write_arming_file(arming_file, armed=True, ts_epoch=time.time())
    monkeypatch.setattr(la, "STATE_PATH", arming_file)
    monkeypatch.delenv("CBP_EXECUTION_ARMED", raising=False)
    monkeypatch.delenv("CBP_LIVE_ENABLED", raising=False)
    monkeypatch.delenv("CBP_EXECUTION_LIVE_ENABLED", raising=False)
    monkeypatch.setenv("CBP_LIVE_ARMING_MAX_AGE_S", "300")

    armed, reason = la.live_armed_signal()

    assert armed is True, f"Expected armed=True for fresh persisted state, got {armed!r}"
    assert "persisted:live_arming.json" in reason, f"Expected persisted source, got {reason!r}"


# ── Test 4 ────────────────────────────────────────────────────────────────

def test_no_env_persisted_armed_stale_returns_not_armed(monkeypatch, tmp_path):
    """No env vars; persisted armed=True but ts older than max_age -> not armed."""
    import services.execution.live_arming as la

    arming_file = tmp_path / "live_arming.json"
    _write_arming_file(arming_file, armed=True, ts_epoch=time.time() - 999.0)
    monkeypatch.setattr(la, "STATE_PATH", arming_file)
    monkeypatch.delenv("CBP_EXECUTION_ARMED", raising=False)
    monkeypatch.delenv("CBP_LIVE_ENABLED", raising=False)
    monkeypatch.delenv("CBP_EXECUTION_LIVE_ENABLED", raising=False)
    monkeypatch.setenv("CBP_LIVE_ARMING_MAX_AGE_S", "300")

    armed, reason = la.live_armed_signal()

    assert armed is False, f"Expected armed=False for stale persisted state, got {armed!r}"
    assert "persisted_stale" in reason, f"Expected persisted_stale in reason, got {reason!r}"


# ── Test 5 ────────────────────────────────────────────────────────────────

def test_corrupt_arming_file_returns_persisted_error(monkeypatch, tmp_path):
    """
    live_arming.json exists but contains invalid JSON.
    live_armed_signal() must return False, reason containing "persisted_error:".
    If "live_not_armed" is returned, the patch was not applied —
    get_live_armed_state() is still swallowing the parse error via _load().
    """
    import services.execution.live_arming as la

    arming_file = tmp_path / "live_arming.json"
    arming_file.parent.mkdir(parents=True, exist_ok=True)
    arming_file.write_text("{invalid json!!!", encoding="utf-8")
    monkeypatch.setattr(la, "STATE_PATH", arming_file)
    monkeypatch.delenv("CBP_EXECUTION_ARMED", raising=False)
    monkeypatch.delenv("CBP_LIVE_ENABLED", raising=False)
    monkeypatch.delenv("CBP_EXECUTION_LIVE_ENABLED", raising=False)

    armed, reason = la.live_armed_signal()

    assert armed is False, f"Expected armed=False for corrupt file, got {armed!r}"
    assert "persisted_error" in reason, (
        f"Expected 'persisted_error' in reason, got {reason!r}\n"
        "If 'live_not_armed': P1D patch not applied."
    )


# ── Test 6 ────────────────────────────────────────────────────────────────

def test_empty_arming_file_returns_persisted_error(monkeypatch, tmp_path):
    """live_arming.json exists but is empty (0 bytes) -> persisted_error."""
    import services.execution.live_arming as la

    arming_file = tmp_path / "live_arming.json"
    arming_file.parent.mkdir(parents=True, exist_ok=True)
    arming_file.write_bytes(b"")
    monkeypatch.setattr(la, "STATE_PATH", arming_file)
    monkeypatch.delenv("CBP_EXECUTION_ARMED", raising=False)
    monkeypatch.delenv("CBP_LIVE_ENABLED", raising=False)
    monkeypatch.delenv("CBP_EXECUTION_LIVE_ENABLED", raising=False)

    armed, reason = la.live_armed_signal()

    assert armed is False, f"Expected armed=False for empty file, got {armed!r}"
    assert "persisted_error" in reason, (
        f"Expected persisted_error for empty file, got {reason!r}"
    )


# ── Test 7 ────────────────────────────────────────────────────────────────

def test_absent_arming_file_returns_not_armed(monkeypatch, tmp_path):
    """
    live_arming.json does not exist; no env vars.
    Must return False without "persisted_error" — absent file is not an error.
    """
    import services.execution.live_arming as la

    arming_file = tmp_path / "live_arming.json"  # not created
    monkeypatch.setattr(la, "STATE_PATH", arming_file)
    monkeypatch.delenv("CBP_EXECUTION_ARMED", raising=False)
    monkeypatch.delenv("CBP_LIVE_ENABLED", raising=False)
    monkeypatch.delenv("CBP_EXECUTION_LIVE_ENABLED", raising=False)

    armed, reason = la.live_armed_signal()

    assert armed is False, f"Expected armed=False when file absent, got {armed!r}"
    assert "persisted_error" not in reason, (
        f"Absent file must not be treated as an error, got {reason!r}"
    )


# ── Test 8 ────────────────────────────────────────────────────────────────

def test_arming_ttl_boundary(monkeypatch, tmp_path):
    """
    age_s > max_age_s is stale; age_s below max_age_s is fresh.
    Uses max_age=60s. Tests max_age+1 (stale) and max_age-1 (fresh).
    """
    import services.execution.live_arming as la

    max_age = 60.0
    arming_file = tmp_path / "live_arming.json"
    monkeypatch.setattr(la, "STATE_PATH", arming_file)
    monkeypatch.delenv("CBP_EXECUTION_ARMED", raising=False)
    monkeypatch.delenv("CBP_LIVE_ENABLED", raising=False)
    monkeypatch.delenv("CBP_EXECUTION_LIVE_ENABLED", raising=False)
    monkeypatch.setenv("CBP_LIVE_ARMING_MAX_AGE_S", str(max_age))

    # max_age + 1s -> stale
    _write_arming_file(arming_file, armed=True, ts_epoch=time.time() - (max_age + 1.0))
    armed, reason = la.live_armed_signal()
    assert armed is False, f"Expected stale at max_age+1s, got armed={armed!r} reason={reason!r}"
    assert "persisted_stale" in reason, f"Expected persisted_stale, got {reason!r}"

    # max_age - 1s -> fresh
    _write_arming_file(arming_file, armed=True, ts_epoch=time.time() - (max_age - 1.0))
    armed2, reason2 = la.live_armed_signal()
    assert armed2 is True, f"Expected armed at max_age-1s, got armed={armed2!r} reason={reason2!r}"
    assert "persisted:live_arming.json" in reason2, f"Expected persisted, got {reason2!r}"
