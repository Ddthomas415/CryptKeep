from __future__ import annotations

import json
import sys
from pathlib import Path

from services.events.platform_event_journal import append_platform_event
from services.events.platform_event_packet import build_platform_event_packet_report

ROOT = Path(__file__).resolve().parents[1]


def test_platform_event_packet_report_passes_when_all_checks_pass(tmp_path):
    path = tmp_path / "platform_events.jsonl"
    append_platform_event(event_type="CampaignStarted", producer="test", commit_sha="abc123", path=path)

    report = build_platform_event_packet_report(path, require_events=True)

    assert report["ok"] is True
    assert report["event_count"] == 1
    assert report["checks"] == {"summary": True, "integrity": True, "secrets": True}
    assert report["summary"]["event_types"] == {"CampaignStarted": 1}
    assert report["integrity"]["finding_count"] == 0
    assert report["secrets"]["finding_count"] == 0


def test_platform_event_packet_report_fails_when_required_events_missing(tmp_path):
    path = tmp_path / "missing.jsonl"

    report = build_platform_event_packet_report(path, require_events=True)

    assert report["ok"] is False
    assert report["checks"] == {"summary": False, "integrity": False, "secrets": False}
    assert report["reasons"]["summary"] == "platform_event_journal_empty"
    assert report["integrity"]["findings"][0]["reason"] == "platform_event_journal_missing"
    assert report["secrets"]["findings"][0]["reason"] == "platform_event_journal_missing"


def test_platform_event_packet_report_fails_on_integrity_or_secret_findings(tmp_path):
    path = tmp_path / "platform_events.jsonl"
    path.write_text(
        json.dumps(
            {
                "schema_version": "platform_event_v1",
                "event_id": "event-1",
                "timestamp": "2026-01-01T00:00:00Z",
                "event_type": "CampaignStarted",
                "producer": "test",
                "source": "test",
                "commit_sha": "abc123",
                "provenance": {},
                "payload": {"api_token": "leaked"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = build_platform_event_packet_report(path, require_events=True)

    assert report["ok"] is False
    assert report["checks"]["summary"] is True
    assert report["checks"]["integrity"] is True
    assert report["checks"]["secrets"] is False
    assert report["secrets"]["findings"][0]["reason"] == "sensitive_key_unredacted"


def test_report_platform_event_packet_cli_writes_evidence(tmp_path, capsys):
    from scripts.report_platform_event_packet import main

    path = tmp_path / "platform_events.jsonl"
    evidence = tmp_path / "evidence"
    append_platform_event(event_type="EvidenceArtifactGenerated", producer="test", commit_sha="abc123", path=path)

    old_argv = sys.argv
    try:
        sys.argv = [
            "report_platform_event_packet.py",
            "--path",
            str(path),
            "--require-events",
            "--evidence-dest",
            str(evidence),
            "--json",
        ]
        assert main() == 0
    finally:
        sys.argv = old_argv

    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["event_count"] == 1
    assert out["evidence_path"].startswith(str(evidence))
    assert len(list(evidence.glob("platform-event-packet-*.json"))) == 1


def test_platform_event_operator_make_targets_are_documented():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    scripts = (ROOT / "scripts" / "SCRIPTS.md").read_text(encoding="utf-8")
    doc = (ROOT / "docs" / "PLATFORM_EVENT_JOURNAL.md").read_text(encoding="utf-8")

    for target in (
        "platform-event-journal",
        "platform-event-journal-json",
        "platform-event-secrets",
        "platform-event-secrets-json",
        "platform-event-integrity",
        "platform-event-integrity-json",
        "platform-event-packet",
        "platform-event-packet-json",
    ):
        assert f"{target}:" in makefile
    for command in (
        "make platform-event-journal",
        "make platform-event-secrets",
        "make platform-event-integrity",
        "make platform-event-packet",
    ):
        assert command in scripts
        assert command in doc
