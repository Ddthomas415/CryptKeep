from __future__ import annotations

import json
import sys

from services.events.platform_event_integrity import check_platform_event_integrity
from services.events.platform_event_journal import append_platform_event


def test_platform_event_integrity_passes_valid_event(tmp_path):
    path = tmp_path / "platform_events.jsonl"
    append_platform_event(
        event_type="StrategySignalProduced",
        producer="test",
        commit_sha="abc123",
        payload={"signal": "long"},
        path=path,
    )

    report = check_platform_event_integrity(path, require_events=True)

    assert report["ok"] is True
    assert report["event_count"] == 1
    assert report["findings"] == []


def test_platform_event_integrity_flags_missing_required_field(tmp_path):
    path = tmp_path / "platform_events.jsonl"
    path.write_text(
        json.dumps(
            {
                "schema_version": "platform_event_v1",
                "event_id": "e1",
                "timestamp": "2026-01-01T00:00:00Z",
                "event_type": "StrategySignalProduced",
                "producer": "test",
                "source": "test",
                "commit_sha": "abc123",
                "payload": {},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = check_platform_event_integrity(path, require_events=True)

    assert report["ok"] is False
    assert any(f["reason"] == "missing_field:provenance" for f in report["findings"])
    assert any(f["reason"] == "invalid_provenance" for f in report["findings"])


def test_platform_event_integrity_flags_bad_schema_values(tmp_path):
    path = tmp_path / "platform_events.jsonl"
    path.write_text(
        json.dumps(
            {
                "schema_version": "other",
                "event_id": "",
                "timestamp": "not-a-time",
                "event_type": "Unknown",
                "producer": "",
                "source": "",
                "commit_sha": "",
                "provenance": [],
                "payload": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = check_platform_event_integrity(path, require_events=True)
    reasons = {f["reason"] for f in report["findings"]}

    assert report["ok"] is False
    assert {
        "invalid_schema_version",
        "missing_event_id",
        "invalid_timestamp",
        "unsupported_event_type",
        "missing_producer",
        "missing_source",
        "missing_commit_sha",
        "invalid_provenance",
        "invalid_payload",
    }.issubset(reasons)


def test_platform_event_integrity_require_events_fails_missing_or_empty(tmp_path):
    missing = tmp_path / "missing.jsonl"
    report = check_platform_event_integrity(missing, require_events=False)
    assert report["ok"] is True
    assert report["exists"] is False

    report = check_platform_event_integrity(missing, require_events=True)
    assert report["ok"] is False
    assert report["findings"][0]["reason"] == "platform_event_journal_missing"

    empty = tmp_path / "empty.jsonl"
    empty.write_text("", encoding="utf-8")
    report = check_platform_event_integrity(empty, require_events=True)
    assert report["ok"] is False
    assert report["findings"][0]["reason"] == "platform_event_journal_empty"


def test_platform_event_integrity_flags_unparseable_json(tmp_path):
    path = tmp_path / "platform_events.jsonl"
    path.write_text("{not-json}\n", encoding="utf-8")

    report = check_platform_event_integrity(path)

    assert report["ok"] is False
    assert report["findings"][0]["reason"] == "platform_event_json_unparseable"
    assert report["findings"][0]["line"] == 1


def test_check_platform_event_integrity_cli_writes_evidence(tmp_path, capsys):
    from scripts.check_platform_event_integrity import main

    path = tmp_path / "platform_events.jsonl"
    evidence = tmp_path / "evidence"
    append_platform_event(event_type="CampaignStarted", producer="test", commit_sha="abc123", path=path)

    old_argv = sys.argv
    try:
        sys.argv = [
            "check_platform_event_integrity.py",
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
    assert len(list(evidence.glob("platform-event-integrity-*.json"))) == 1

