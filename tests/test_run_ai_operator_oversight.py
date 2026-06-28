from __future__ import annotations

import json

from scripts import run_ai_operator_oversight as script


def test_run_ai_operator_oversight_outputs_json_without_write(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        script,
        "build_operator_oversight_report",
        lambda *, use_ai=False: {
            "report_type": "ai_operator_oversight",
            "status": "paper_gate_blocked",
            "watch_report_status": "available",
            "read_only": True,
            "machine_summary": "summary",
            "ai_summary": {"status": "machine_only"},
            "action_items": [],
        },
    )
    monkeypatch.setattr(
        script,
        "write_operator_oversight_report",
        lambda _report: (_ for _ in ()).throw(AssertionError("must not write")),
    )

    assert script.main(["--json", "--no-write"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["report_type"] == "ai_operator_oversight"
    assert out["read_only"] is True


def test_run_ai_operator_oversight_writes_by_default(monkeypatch, capsys) -> None:
    seen: dict[str, object] = {}

    def _build(*, use_ai=False):
        seen["use_ai"] = use_ai
        return {
            "report_type": "ai_operator_oversight",
            "status": "paper_gate_blocked",
            "watch_report_status": "available",
            "read_only": True,
            "machine_summary": "summary",
            "ai_summary": {"status": "machine_only"},
            "action_items": [{"id": "paper_gate_blocker", "severity": "info", "summary": "blocked"}],
        }

    def _write(report):
        seen["report"] = report
        return {"latest_json": "/tmp/latest.json", "latest_markdown": "/tmp/latest.md"}

    monkeypatch.setattr(script, "build_operator_oversight_report", _build)
    monkeypatch.setattr(script, "write_operator_oversight_report", _write)

    assert script.main(["--use-ai"]) == 0
    out = capsys.readouterr().out
    assert seen["use_ai"] is True
    assert "artifact_latest_json=/tmp/latest.json" in out
