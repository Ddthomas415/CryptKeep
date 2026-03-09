from __future__ import annotations

from services.admin import service_controls
from services.admin import watchdog as admin_watchdog


def test_service_controls_rejects_unsafe_name():
    out = service_controls.stop_service_from_pidfile("../bad-name")
    assert out.get("ok") is False
    assert out.get("error") == "unsafe_service_name"


def test_service_controls_rejects_unknown_name():
    out = service_controls.stop_service_from_pidfile("nonexistent_service")
    assert out.get("ok") is False
    assert out.get("error") == "unknown_service_name"


def test_service_controls_pid_file_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(admin_watchdog, "PID_DIR", tmp_path)
    out = service_controls.stop_service_from_pidfile("market_data_poller")
    assert out.get("ok") is True
    assert out.get("note") == "pid_file_missing"


def test_service_controls_invalid_pid_file_is_removed(monkeypatch, tmp_path):
    monkeypatch.setattr(admin_watchdog, "PID_DIR", tmp_path)
    pf = tmp_path / "market_data_poller.pid"
    pf.parent.mkdir(parents=True, exist_ok=True)
    pf.write_text("not-an-int", encoding="utf-8")

    out = service_controls.stop_service_from_pidfile("market_data_poller")
    assert out.get("ok") is False
    assert out.get("error") == "invalid_pid_file"
    assert not pf.exists()


def test_service_controls_accepts_registered_service_name(monkeypatch, tmp_path):
    monkeypatch.setattr(admin_watchdog, "PID_DIR", tmp_path)
    out = service_controls.stop_service_from_pidfile("ops_risk_gate")
    assert out.get("ok") is True
    assert out.get("note") == "pid_file_missing"

def test_service_controls_still_alive(monkeypatch, tmp_path):
    from services.admin import health
    from services.admin import service_controls as sc
    from services.admin import watchdog

    pid_dir = tmp_path / "pids"
    pid_dir.mkdir(parents=True, exist_ok=True)
    pf = pid_dir / "market_data_poller.pid"
    pf.write_text("12345", encoding="utf-8")

    health_calls = []

    monkeypatch.setattr(watchdog, "PID_DIR", pid_dir)
    monkeypatch.setattr(sc.os, "kill", lambda pid, sig: None)
    monkeypatch.setattr(sc.time, "sleep", lambda *_: None)
    monkeypatch.setattr(watchdog, "_pid_alive", lambda pid: True)
    monkeypatch.setattr(
        health,
        "set_health",
        lambda *args, **kwargs: health_calls.append((args, kwargs)),
    )

    out = sc.stop_service_from_pidfile("market_data_poller")

    assert out["ok"] is False
    assert out["still_alive"]
    assert out["still_alive"][0]["service"] == "market_data_poller"
    assert pf.exists()
    assert any(
        args[:2] == ("market_data_poller", "RUNNING")
        for args, kwargs in health_calls
    )


def test_service_controls_kill_failed(monkeypatch, tmp_path):
    from services.admin import health
    from services.admin import service_controls as sc
    from services.admin import watchdog

    pid_dir = tmp_path / "pids"
    pid_dir.mkdir(parents=True, exist_ok=True)
    pf = pid_dir / "market_data_poller.pid"
    pf.write_text("12345", encoding="utf-8")

    monkeypatch.setattr(watchdog, "PID_DIR", pid_dir)
    def _kill(pid, sig):
        if sig == sc.signal.SIGTERM:
            return None
        raise PermissionError("denied")

    monkeypatch.setattr(sc.os, "kill", _kill)
    monkeypatch.setattr(sc.time, "sleep", lambda *_: None)
    monkeypatch.setattr(watchdog, "_pid_alive", lambda pid: True)
    monkeypatch.setattr(health, "set_health", lambda *args, **kwargs: None)

    out = sc.stop_service_from_pidfile("market_data_poller")

    assert out["ok"] is False
    assert out["errors"]
    assert "kill_failed:" in out["errors"][0]["error"]
    assert out["errors"][0]["service"] == "market_data_poller"
    assert pf.exists()
