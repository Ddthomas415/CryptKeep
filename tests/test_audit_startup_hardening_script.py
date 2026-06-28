from __future__ import annotations

import json

from scripts import audit_startup_hardening as script


def test_audit_startup_hardening_outputs_json_without_write(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        script,
        "build_startup_hardening_audit",
        lambda: {
            "report_type": "startup_hardening_audit",
            "gap_status": "insufficient_evidence",
            "read_only": True,
            "machine_summary": "summary",
            "action_items": [],
        },
    )
    monkeypatch.setattr(
        script,
        "write_startup_hardening_audit",
        lambda _report: (_ for _ in ()).throw(AssertionError("must not write")),
    )

    assert script.main(["--json", "--no-write"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["report_type"] == "startup_hardening_audit"
    assert out["read_only"] is True


def test_audit_startup_hardening_writes_by_default(monkeypatch, capsys) -> None:
    seen: dict[str, object] = {}

    def _build():
        return {
            "report_type": "startup_hardening_audit",
            "gap_status": "insufficient_evidence",
            "read_only": True,
            "machine_summary": "summary",
            "action_items": [{"id": "review_unwrapped_startup_commands", "severity": "warn", "summary": "review"}],
        }

    def _write(report):
        seen["report"] = report
        return {"latest_json": "/tmp/latest.json", "latest_markdown": "/tmp/latest.md"}

    monkeypatch.setattr(script, "build_startup_hardening_audit", _build)
    monkeypatch.setattr(script, "write_startup_hardening_audit", _write)

    assert script.main([]) == 0
    out = capsys.readouterr().out
    assert seen["report"]["report_type"] == "startup_hardening_audit"
    assert "artifact_latest_json=/tmp/latest.json" in out
