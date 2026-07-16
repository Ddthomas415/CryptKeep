from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.audit.operator_event_journal import load_operator_events
from services.audit.operator_event_secret_scan import scan_operator_event_journal
from services.ai_copilot.report_audit import record_ai_copilot_report_write


def test_record_ai_copilot_report_write_metadata_only(monkeypatch):
    calls: list[dict[str, Any]] = []

    def _append_operator_event(**kwargs):
        calls.append(kwargs)
        return {"event_id": "evt-report", "path": "/tmp/operator_events.jsonl"}

    monkeypatch.setattr("services.ai_copilot.report_audit.append_operator_event", _append_operator_event)

    result = record_ai_copilot_report_write(
        report_type="simulation_run",
        report={"severity": "warn", "stdout": "REPORT_CONTENT_DO_NOT_LOG"},
        paths={
            "json_path": "/tmp/ai_reports/simulation_test.json",
            "markdown_path": "/tmp/ai_reports/simulation_test.md",
        },
        source="tests",
    )

    assert result == {"ok": True, "event_id": "evt-report", "path": "/tmp/operator_events.jsonl"}
    event = calls[0]
    assert event["action"] == "ai_copilot_report_write"
    assert event["target"] == "ai_copilot_report:simulation_run"
    assert event["post_state"] == {
        "report_type": "simulation_run",
        "status": "warn",
        "artifact_count": 2,
        "artifact_keys": ["json_path", "markdown_path"],
        "artifact_names": ["simulation_test.json", "simulation_test.md"],
    }
    assert event["extra"] == {"report_payload_logged": False, "artifact_content_logged": False}
    assert "REPORT_CONTENT_DO_NOT_LOG" not in json.dumps(event, sort_keys=True)


def test_simulation_report_write_appends_real_metadata_event(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    from services.ai_copilot.sim_runner import write_simulation_report

    report = {
        "generated_at": "2026-07-16T00:00:00Z",
        "job": "paper_diagnostics",
        "severity": "ok",
        "ok": True,
        "summary": "SIM_SUMMARY_DO_NOT_LOG",
        "command": ["python", "scripts/report_paper_run_diagnostics.py"],
        "stdout": "STDOUT_DO_NOT_LOG",
        "stderr": "STDERR_DO_NOT_LOG",
        "recommendations": ["REC_DO_NOT_LOG"],
    }

    paths = write_simulation_report(report, stem="simulation_test")

    assert paths["operator_event"]["ok"] is True
    events = load_operator_events()
    assert len(events) == 1
    event = events[0]
    assert event["action"] == "ai_copilot_report_write"
    assert event["target"] == "ai_copilot_report:simulation_run"
    assert event["post_state"]["artifact_names"] == ["simulation_test.json", "simulation_test.md"]
    raw = Path(paths["operator_event"]["path"]).read_text(encoding="utf-8")
    assert "STDOUT_DO_NOT_LOG" not in raw
    assert "STDERR_DO_NOT_LOG" not in raw
    assert "SIM_SUMMARY_DO_NOT_LOG" not in raw
    assert scan_operator_event_journal(require_events=True)["ok"] is True


def test_all_ai_copilot_report_writers_return_operator_event(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    import services.ai_copilot.drift_auditor as drift
    import services.ai_copilot.operator_oversight as oversight
    import services.ai_copilot.pr_reviewer as pr
    import services.ai_copilot.safety_auditor as safety
    import services.ai_copilot.sim_runner as sim
    import services.ai_copilot.strategy_lab as lab

    calls: list[tuple[str, str, tuple[str, ...]]] = []

    def _record(*, report_type, report, paths, source):
        calls.append((report_type, source, tuple(sorted(paths.keys()))))
        return {"ok": True, "event_id": f"evt-{report_type}", "path": "/tmp/operator_events.jsonl"}

    for module in (drift, oversight, pr, safety, sim, lab):
        monkeypatch.setattr(module, "record_ai_copilot_report_write", _record)

    outputs = [
        pr.write_review_report(pr.build_review_packet(changed_files=["docs/x.md"]), stem="review_test"),
        sim.write_simulation_report({"severity": "ok", "ok": True, "recommendations": []}, stem="simulation_test"),
        lab.write_strategy_lab_report({"severity": "ok", "ok": True, "recommendations": []}, stem="strategy_lab_test"),
        drift.write_drift_report({"severity": "ok", "ok": True, "checks": [], "issues": [], "recommendations": []}, stem="drift_test"),
        safety.write_safety_report({"severity": "ok", "ok": True, "checks": [], "recommendations": []}, stem="safety_test"),
        oversight.write_operator_oversight_report({"report_type": "ai_operator_oversight", "machine_facts": {}, "do_not_touch": []}),
    ]

    assert all(output["operator_event"]["ok"] is True for output in outputs)
    assert [call[0] for call in calls] == [
        "repo_review",
        "simulation_run",
        "strategy_lab",
        "drift_audit",
        "safety_audit",
        "ai_operator_oversight",
    ]
    assert calls[-1][2] == ("dated_json", "dated_markdown", "latest_json", "latest_markdown")
