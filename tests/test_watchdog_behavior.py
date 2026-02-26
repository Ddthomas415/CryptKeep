from __future__ import annotations

import json
import time

from services.process import watchdog


def test_watchdog_stale_heartbeat_triggers_snapshot_and_kill_switch(monkeypatch, tmp_path):
    wd_file = tmp_path / "watchdog_last.json"
    now = time.time()

    monkeypatch.setattr(watchdog, "WD_PATH", wd_file)
    monkeypatch.setattr(
        watchdog,
        "_cfg",
        lambda: {
            "enabled": True,
            "stale_after_sec": 60,
            "auto_stop_on_stale": False,
            "write_crash_snapshot_on_stale": True,
        },
    )
    monkeypatch.setattr(
        watchdog,
        "bot_status",
        lambda: {"running": True, "pid": 1234, "state": {"mode": "paper"}},
    )
    monkeypatch.setattr(watchdog, "read_heartbeat", lambda: {"ts_epoch": now - 120})
    monkeypatch.setattr(watchdog, "write_crash_snapshot", lambda **kwargs: {"ok": True, "kwargs": kwargs})
    monkeypatch.setattr(watchdog, "_kill_switch_on", lambda reason: {"ok": True, "reason": reason})

    out = watchdog.run_watchdog_once()

    assert out.get("ok") is True
    assert out.get("triggered") is True
    assert out.get("heartbeat_stale") is True
    actions = [a.get("action") for a in out.get("actions", [])]
    assert actions == ["write_crash_snapshot", "kill_switch_on"]
    assert wd_file.exists()
    persisted = json.loads(wd_file.read_text(encoding="utf-8"))
    assert persisted.get("triggered") is True


def test_watchdog_healthy_heartbeat_no_action(monkeypatch, tmp_path):
    wd_file = tmp_path / "watchdog_last.json"
    now = time.time()

    monkeypatch.setattr(watchdog, "WD_PATH", wd_file)
    monkeypatch.setattr(
        watchdog,
        "_cfg",
        lambda: {
            "enabled": True,
            "stale_after_sec": 60,
            "auto_stop_on_stale": False,
            "write_crash_snapshot_on_stale": True,
        },
    )
    monkeypatch.setattr(
        watchdog,
        "bot_status",
        lambda: {"running": True, "pid": 1234, "state": {}},
    )
    monkeypatch.setattr(watchdog, "read_heartbeat", lambda: {"ts_epoch": now - 5})

    out = watchdog.run_watchdog_once()

    assert out.get("ok") is True
    assert out.get("triggered") is False
    assert out.get("heartbeat_stale") is False
    assert out.get("actions") == []
    assert wd_file.exists()


def test_watchdog_auto_stop_calls_stop_bot(monkeypatch, tmp_path):
    wd_file = tmp_path / "watchdog_last.json"
    now = time.time()
    called = {"stop": 0}

    monkeypatch.setattr(watchdog, "WD_PATH", wd_file)
    monkeypatch.setattr(
        watchdog,
        "_cfg",
        lambda: {
            "enabled": True,
            "stale_after_sec": 10,
            "auto_stop_on_stale": True,
            "stop_hard": True,
            "write_crash_snapshot_on_stale": False,
        },
    )
    monkeypatch.setattr(
        watchdog,
        "bot_status",
        lambda: {"running": True, "pid": 777, "state": {}},
    )
    monkeypatch.setattr(watchdog, "read_heartbeat", lambda: {"ts_epoch": now - 120})
    monkeypatch.setattr(watchdog, "_kill_switch_on", lambda reason: {"ok": True, "reason": reason})

    def _stop_bot(*, hard: bool = True):
        called["stop"] += 1
        return {"ok": True, "hard": hard}

    monkeypatch.setattr(watchdog, "stop_bot", _stop_bot)

    out = watchdog.run_watchdog_once()

    assert out.get("triggered") is True
    assert called["stop"] == 1
    actions = [a.get("action") for a in out.get("actions", [])]
    assert actions == ["kill_switch_on", "stop_bot"]
