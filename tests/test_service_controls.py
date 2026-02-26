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
