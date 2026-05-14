from __future__ import annotations

import json

from services.ai_copilot import alert_monitor_status as monitor_status


def test_load_runtime_status_reads_health_payload(tmp_path, monkeypatch):
    runtime = tmp_path / "runtime"
    health = runtime / "health"
    health.mkdir(parents=True, exist_ok=True)
    (health / "ai_alert_monitor.json").write_text(
        json.dumps({"ok": True, "status": "idle", "pid": 123, "incidents_written": 4}),
        encoding="utf-8",
    )
    (health / "ai_alert_monitor.pid.json").write_text(json.dumps({"pid": 123}), encoding="utf-8")
    monkeypatch.setattr(monitor_status, "runtime_dir", lambda: runtime)

    out = monitor_status.load_runtime_status()

    assert out["ok"] is True
    assert out["status"] == "idle"
    assert out["pid"] == 123
    assert out["incidents_written"] == 4
    assert out["has_status"] is True
    assert out["has_pid_file"] is True


def test_list_recent_incidents_returns_latest_first(tmp_path, monkeypatch):
    runtime = tmp_path / "runtime"
    reports = runtime / "ai_reports"
    reports.mkdir(parents=True, exist_ok=True)
    for stem in ["ai_alert_monitor_20260512T165512Z", "ai_alert_monitor_20260512T165742Z"]:
        (reports / f"{stem}.json").write_text(
            json.dumps({"severity": "warn", "summary": stem, "generated_at": stem}),
            encoding="utf-8",
        )
    monkeypatch.setattr(monitor_status, "runtime_dir", lambda: runtime)

    out = monitor_status.list_recent_incidents(limit=2)

    assert [row["stem"] for row in out] == [
        "ai_alert_monitor_20260512T165742Z",
        "ai_alert_monitor_20260512T165512Z",
    ]


def test_request_stop_writes_stop_file(tmp_path, monkeypatch):
    runtime = tmp_path / "runtime"
    monkeypatch.setattr(monitor_status, "runtime_dir", lambda: runtime)
    monkeypatch.setattr(monitor_status, "ensure_dirs", lambda: None)

    out = monitor_status.request_stop()

    assert out["ok"] is True
    assert (runtime / "flags" / "ai_alert_monitor.stop").exists()
