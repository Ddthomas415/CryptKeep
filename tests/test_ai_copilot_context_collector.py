from __future__ import annotations

import json

from services.ai_copilot.context_collector import collect_incident_context


def test_collect_incident_context_includes_runtime_logs_and_alerts(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    runtime = tmp_path / "runtime"
    (runtime / "flags").mkdir(parents=True, exist_ok=True)
    (runtime / "logs").mkdir(parents=True, exist_ok=True)
    (runtime / "alerts").mkdir(parents=True, exist_ok=True)
    (runtime / "system_guard.json").write_text(json.dumps({"state": "RUNNING"}), encoding="utf-8")
    (runtime / "kill_switch.json").write_text(json.dumps({"armed": False}), encoding="utf-8")
    (runtime / "logs" / "pipeline.log").write_text("Traceback line\n", encoding="utf-8")
    (runtime / "alerts" / "critical_alerts.jsonl").write_text(
        json.dumps({"level": "error", "message": "pipeline down"}) + "\n",
        encoding="utf-8",
    )

    context = collect_incident_context()

    assert "Recent Alerts" in context
    assert "pipeline down" in context
    assert "Recent Runtime Logs" in context
    assert "pipeline.log" in context


def test_collect_incident_context_falls_back_to_legacy_flag_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    runtime = tmp_path / "runtime"
    (runtime / "flags").mkdir(parents=True, exist_ok=True)

    (runtime / "flags" / "system_guard.json").write_text(json.dumps({"state": "HALTED"}), encoding="utf-8")
    (runtime / "flags" / "kill_switch.json").write_text(json.dumps({"armed": True}), encoding="utf-8")

    context = collect_incident_context()

    assert '"state": "HALTED"' in context
    assert '"armed": true' in context
