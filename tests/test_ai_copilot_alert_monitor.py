from __future__ import annotations

import json
from pathlib import Path

from services.ai_copilot import alert_monitor


def test_process_once_writes_incident_report_from_new_alert(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    runtime_alerts = tmp_path / "runtime" / "alerts"
    runtime_logs = tmp_path / "runtime" / "logs"
    runtime_alerts.mkdir(parents=True, exist_ok=True)
    runtime_logs.mkdir(parents=True, exist_ok=True)
    (runtime_alerts / "critical_alerts.jsonl").write_text(
        json.dumps({"ts": "2026-05-06T12:00:00Z", "level": "error", "message": "pipeline exited"}) + "\n",
        encoding="utf-8",
    )
    (runtime_logs / "pipeline.log").write_text("Traceback: NetworkError\n", encoding="utf-8")

    monkeypatch.setattr(
        alert_monitor,
        "canonical_service_status",
        lambda: {
            "pipeline": {"running": False, "pid": None},
            "executor": {"running": True, "pid": 123},
        },
    )
    monkeypatch.setattr(alert_monitor, "read_heartbeat", lambda: {"source": "pipeline", "ts_epoch": 1.0})
    monkeypatch.setattr(alert_monitor, "get_system_health", lambda: {"state": "DEGRADED", "reasons": ["pipeline_down"]})
    monkeypatch.setattr(
        alert_monitor,
        "analyze_incident",
        lambda **_: {
            "ok": True,
            "analysis": "AI summary",
            "provider": "openai",
            "model": "gpt-test",
            "context_chars": 100,
        },
    )

    out = alert_monitor.process_once()

    assert out["status"] == "incident_written"
    rows = alert_monitor.list_recent_incidents(limit=5)
    assert rows
    payload = rows[0]["payload"]
    assert payload["monitor_name"] == alert_monitor.MONITOR_NAME
    assert payload["analysis"] == "AI summary"
    assert any(event["event_type"] == "alert" for event in payload["events"])
    status = alert_monitor.load_runtime_status()
    assert status["last_report_stem"] == out["report_stem"]


def test_process_once_idle_without_new_events(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    monkeypatch.setattr(alert_monitor, "canonical_service_status", lambda: {"executor": {"running": True, "pid": 123}})
    monkeypatch.setattr(alert_monitor, "read_heartbeat", lambda: {"source": "executor", "ts_epoch": 1.0})
    monkeypatch.setattr(alert_monitor, "get_system_health", lambda: {"state": "HEALTHY"})
    monkeypatch.setattr(alert_monitor, "analyze_incident", lambda **_: (_ for _ in ()).throw(AssertionError("should not analyze")))

    out = alert_monitor.process_once()

    assert out["status"] == "idle"
    assert out["reason"] == "no_new_events"


def test_process_once_falls_back_when_copilot_unavailable(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    runtime_alerts = tmp_path / "runtime" / "alerts"
    runtime_alerts.mkdir(parents=True, exist_ok=True)
    (runtime_alerts / "critical_alerts.jsonl").write_text(
        json.dumps({"ts": "2026-05-06T12:00:00Z", "level": "error", "message": "reconciler failed"}) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(alert_monitor, "canonical_service_status", lambda: {"reconciler": {"running": False, "pid": None}})
    monkeypatch.setattr(alert_monitor, "read_heartbeat", lambda: {"source": "reconciler", "ts_epoch": 1.0})
    monkeypatch.setattr(alert_monitor, "get_system_health", lambda: {"state": "DEGRADED"})
    monkeypatch.setattr(alert_monitor, "analyze_incident", lambda **_: {"ok": False, "error": "Missing API key"})

    out = alert_monitor.process_once()

    assert out["status"] == "incident_written"
    rows = alert_monitor.list_recent_incidents(limit=1)
    assert rows[0]["payload"]["analysis_mode"] == "heuristic_fallback"
    assert "Missing API key" in rows[0]["payload"]["analysis"]
