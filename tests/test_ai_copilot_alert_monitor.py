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
    monkeypatch.setattr(
        alert_monitor,
        "load_runtime_trading_config",
        lambda: {
            "mode": "paper",
            "execution": {"executor_mode": "paper", "live_enabled": False},
            "live": {"enabled": False},
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
    monkeypatch.setattr(
        alert_monitor,
        "load_runtime_trading_config",
        lambda: {
            "mode": "paper",
            "execution": {"executor_mode": "paper", "live_enabled": False},
            "live": {"enabled": False},
        },
    )
    monkeypatch.setattr(alert_monitor, "read_heartbeat", lambda: {"source": "executor", "ts_epoch": 1.0})
    monkeypatch.setattr(alert_monitor, "get_system_health", lambda: {"state": "HEALTHY"})
    monkeypatch.setattr(alert_monitor, "analyze_incident", lambda **_: (_ for _ in ()).throw(AssertionError("should not analyze")))

    out = alert_monitor.process_once()

    assert out["status"] == "idle"
    assert out["reason"] == "no_new_events"


def test_process_once_idle_preserves_loop_progress_metadata(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    monkeypatch.setattr(alert_monitor, "canonical_service_status", lambda: {"executor": {"running": True, "pid": 123}})
    monkeypatch.setattr(
        alert_monitor,
        "load_runtime_trading_config",
        lambda: {
            "mode": "paper",
            "execution": {"executor_mode": "paper", "live_enabled": False},
            "live": {"enabled": False},
        },
    )
    monkeypatch.setattr(alert_monitor, "read_heartbeat", lambda: {"source": "executor", "ts_epoch": 1.0})
    monkeypatch.setattr(alert_monitor, "get_system_health", lambda: {"state": "HEALTHY"})
    monkeypatch.setattr(alert_monitor, "analyze_incident", lambda **_: (_ for _ in ()).throw(AssertionError("should not analyze")))

    out = alert_monitor.process_once(
        status_context={
            "loops": 17,
            "errors": 2,
            "incidents_written": 3,
            "pid": 456,
            "poll_interval_sec": 30.0,
        }
    )

    assert out["status"] == "idle"
    status = alert_monitor.load_runtime_status()
    assert status["status"] == "idle"
    assert status["loops"] == 17
    assert status["errors"] == 2
    assert status["incidents_written"] == 3
    assert status["pid"] == 456
    assert status["poll_interval_sec"] == 30.0


def test_load_runtime_status_backfills_latest_report_metadata(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    reports = tmp_path / "runtime" / "ai_reports"
    health = tmp_path / "runtime" / "health"
    reports.mkdir(parents=True, exist_ok=True)
    health.mkdir(parents=True, exist_ok=True)

    stem = "ai_alert_monitor_20260507T150000Z"
    payload = {
        "monitor_name": alert_monitor.MONITOR_NAME,
        "generated_at": "2026-05-07T15:00:00+00:00",
        "severity": "critical",
        "summary": "pipeline down",
        "events": [{"event_type": "service_down", "service": "pipeline"}],
    }
    (reports / f"{stem}.json").write_text(json.dumps(payload) + "\n", encoding="utf-8")
    (reports / f"{stem}.md").write_text("# incident\n", encoding="utf-8")
    (health / "ai_alert_monitor.json").write_text(
        json.dumps(
            {
                "ok": True,
                "has_status": True,
                "status": "idle",
                "incidents_written": 1,
                "last_report_stem": "",
                "loops": 5,
                "pid": 321,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (health / "ai_alert_monitor.pid.json").write_text(
        json.dumps({"pid": 321, "started_ts": "2026-05-07T14:59:00+00:00", "poll_interval_sec": 30.0}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(alert_monitor, "_process_alive", lambda pid: pid == 321)

    status = alert_monitor.load_runtime_status()

    assert status["last_report_stem"] == stem
    assert status["last_severity"] == "critical"
    assert status["last_summary"] == "pipeline down"
    assert status["last_event_count"] == 1
    assert status["json_path"].endswith(f"{stem}.json")
    assert status["markdown_path"].endswith(f"{stem}.md")


def test_process_once_idle_restores_report_pointer_after_blank_restart_status(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    reports = tmp_path / "runtime" / "ai_reports"
    health = tmp_path / "runtime" / "health"
    reports.mkdir(parents=True, exist_ok=True)
    health.mkdir(parents=True, exist_ok=True)

    stem = "ai_alert_monitor_20260507T160000Z"
    payload = {
        "monitor_name": alert_monitor.MONITOR_NAME,
        "generated_at": "2026-05-07T16:00:00+00:00",
        "severity": "warn",
        "summary": "log burst",
        "events": [{"event_type": "log_match", "log": "pipeline.log"}],
    }
    (reports / f"{stem}.json").write_text(json.dumps(payload) + "\n", encoding="utf-8")
    (reports / f"{stem}.md").write_text("# incident\n", encoding="utf-8")
    (health / "ai_alert_monitor.json").write_text(
        json.dumps(
            {
                "ok": True,
                "has_status": True,
                "status": "running",
                "incidents_written": 1,
                "last_report_stem": "",
                "loops": 0,
                "errors": 0,
                "pid": 654,
                "poll_interval_sec": 30.0,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (health / "ai_alert_monitor.pid.json").write_text(
        json.dumps({"pid": 654, "started_ts": "2026-05-07T15:59:00+00:00", "poll_interval_sec": 30.0}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(alert_monitor, "_process_alive", lambda pid: pid == 654)
    monkeypatch.setattr(alert_monitor, "canonical_service_status", lambda: {"executor": {"running": True, "pid": 123}})
    monkeypatch.setattr(
        alert_monitor,
        "load_runtime_trading_config",
        lambda: {
            "mode": "paper",
            "execution": {"executor_mode": "paper", "live_enabled": False},
            "live": {"enabled": False},
        },
    )
    monkeypatch.setattr(alert_monitor, "read_heartbeat", lambda: {"source": "executor", "ts_epoch": 1.0})
    monkeypatch.setattr(alert_monitor, "get_system_health", lambda: {"state": "HEALTHY"})
    monkeypatch.setattr(alert_monitor, "analyze_incident", lambda **_: (_ for _ in ()).throw(AssertionError("should not analyze")))

    out = alert_monitor.process_once(
        status_context={
            "loops": 8,
            "errors": 0,
            "incidents_written": 1,
            "pid": 654,
            "poll_interval_sec": 30.0,
        }
    )

    assert out["status"] == "idle"
    status = alert_monitor.load_runtime_status()
    assert status["last_report_stem"] == stem
    assert status["last_summary"] == "log burst"
    assert status["loops"] == 8


def test_process_once_falls_back_when_copilot_unavailable(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    runtime_alerts = tmp_path / "runtime" / "alerts"
    runtime_alerts.mkdir(parents=True, exist_ok=True)
    (runtime_alerts / "critical_alerts.jsonl").write_text(
        json.dumps({"ts": "2026-05-06T12:00:00Z", "level": "error", "message": "reconciler failed"}) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(alert_monitor, "canonical_service_status", lambda: {"reconciler": {"running": False, "pid": None}})
    monkeypatch.setattr(
        alert_monitor,
        "load_runtime_trading_config",
        lambda: {
            "mode": "live",
            "execution": {"executor_mode": "live", "live_enabled": True},
            "live": {"enabled": True},
        },
    )
    monkeypatch.setattr(alert_monitor, "read_heartbeat", lambda: {"source": "reconciler", "ts_epoch": 1.0})
    monkeypatch.setattr(alert_monitor, "get_system_health", lambda: {"state": "DEGRADED"})
    monkeypatch.setattr(alert_monitor, "analyze_incident", lambda **_: {"ok": False, "error": "Missing API key"})

    out = alert_monitor.process_once()

    assert out["status"] == "incident_written"
    rows = alert_monitor.list_recent_incidents(limit=1)
    assert rows[0]["payload"]["analysis_mode"] == "heuristic_fallback"
    assert "Missing API key" in rows[0]["payload"]["analysis"]


def test_process_once_ignores_live_only_services_when_paper_mode_expected(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    monkeypatch.setattr(
        alert_monitor,
        "canonical_service_status",
        lambda: {
            "pipeline": {"running": True, "pid": 100},
            "executor": {"running": True, "pid": 101},
            "ops_signal_adapter": {"running": True, "pid": 102},
            "ops_risk_gate": {"running": True, "pid": 103},
            "intent_consumer": {"running": False, "pid": None},
            "reconciler": {"running": False, "pid": None},
            "market_ws": {"running": False, "pid": None},
        },
    )
    monkeypatch.setattr(
        alert_monitor,
        "load_runtime_trading_config",
        lambda: {
            "mode": "paper",
            "execution": {"executor_mode": "paper", "live_enabled": False},
            "live": {"enabled": False},
        },
    )
    monkeypatch.setattr(alert_monitor, "read_heartbeat", lambda: {"source": "executor", "ts_epoch": 1.0})
    monkeypatch.setattr(alert_monitor, "get_system_health", lambda: {"state": "HEALTHY"})
    monkeypatch.setattr(alert_monitor, "analyze_incident", lambda **_: (_ for _ in ()).throw(AssertionError("should not analyze")))

    out = alert_monitor.process_once()

    assert out["status"] == "idle"
    assert out["reason"] == "no_new_events"
