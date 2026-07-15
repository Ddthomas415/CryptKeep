from __future__ import annotations

import json
import sys

from services.audit.operator_event_journal import append_operator_event
from services.audit.operator_event_secret_scan import scan_operator_event_journal


def test_operator_event_secret_scan_passes_redacted_payload(tmp_path):
    path = tmp_path / "operator_events.jsonl"
    append_operator_event(
        actor="operator",
        action="rotate_secret",
        target="coinbase",
        result="success",
        pre_state={"api_key": "old", "safe": "kept"},
        path=path,
    )

    report = scan_operator_event_journal(path, require_events=True)

    assert report["ok"] is True
    assert report["event_count"] == 1
    assert report["findings"] == []


def test_operator_event_secret_scan_flags_unredacted_sensitive_key_without_value(tmp_path):
    path = tmp_path / "operator_events.jsonl"
    secret_value = "super-secret-value"
    path.write_text(
        json.dumps(
            {
                "actor": "operator",
                "timestamp": "2026-07-15T00:00:00Z",
                "action": "manual",
                "target": "launch_packet",
                "pre_state": {"nested": {"api_token": secret_value}},
                "post_state": {},
                "result": "recorded",
                "reason": "fixture",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = scan_operator_event_journal(path, require_events=True)

    assert report["ok"] is False
    assert report["finding_count"] == 1
    finding = report["findings"][0]
    assert finding["path"] == "pre_state.nested.api_token"
    assert finding["reason"] == "sensitive_key_unredacted"
    assert finding["value"] == {"type": "str", "length": len(secret_value)}
    assert secret_value not in json.dumps(report)


def test_operator_event_secret_scan_require_events_fails_missing_or_empty(tmp_path):
    missing = tmp_path / "missing.jsonl"
    report = scan_operator_event_journal(missing, require_events=False)
    assert report["ok"] is True
    assert report["exists"] is False

    report = scan_operator_event_journal(missing, require_events=True)
    assert report["ok"] is False
    assert report["findings"][0]["reason"] == "operator_event_journal_missing"

    empty = tmp_path / "empty.jsonl"
    empty.write_text("", encoding="utf-8")
    report = scan_operator_event_journal(empty, require_events=True)
    assert report["ok"] is False
    assert report["findings"][0]["reason"] == "operator_event_journal_empty"


def test_operator_event_secret_scan_flags_unparseable_json(tmp_path):
    path = tmp_path / "operator_events.jsonl"
    path.write_text("{not-json}\n", encoding="utf-8")

    report = scan_operator_event_journal(path)

    assert report["ok"] is False
    assert report["findings"][0]["reason"] == "operator_event_json_unparseable"
    assert report["findings"][0]["line"] == 1


def test_check_operator_event_secrets_cli_writes_evidence(tmp_path, capsys):
    from scripts.check_operator_event_secrets import main

    path = tmp_path / "operator_events.jsonl"
    evidence = tmp_path / "evidence"
    append_operator_event(
        actor="operator",
        action="note",
        target="launch_packet",
        result="recorded",
        extra={"token": "redacted by writer"},
        path=path,
    )

    old_argv = sys.argv
    try:
        sys.argv = [
            "check_operator_event_secrets.py",
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
    assert len(list(evidence.glob("operator-event-secret-scan-*.json"))) == 1
