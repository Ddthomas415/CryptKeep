from __future__ import annotations

import json
import subprocess
import sys

import pytest

from services.audit.operator_event_journal import (
    OperatorEventJournalError,
    append_operator_event,
    build_operator_event,
    load_operator_events,
)


def test_operator_event_journal_appends_required_fields_and_reads_back(tmp_path):
    path = tmp_path / "operator_events.jsonl"

    event = append_operator_event(
        actor="operator",
        action="halt",
        target="live_trading",
        result="success",
        reason="drill",
        pre_state={"state": "RUNNING"},
        post_state={"state": "HALTED"},
        path=path,
    )

    assert event["path"] == str(path)
    loaded = load_operator_events(path)
    assert len(loaded) == 1
    row = loaded[0]
    for field in ("actor", "timestamp", "action", "target", "pre_state", "post_state", "result", "reason"):
        assert field in row
    assert row["actor"] == "operator"
    assert row["action"] == "halt"
    assert row["target"] == "live_trading"
    assert row["result"] == "success"


def test_operator_event_journal_redacts_sensitive_payload_fields():
    event = build_operator_event(
        actor="operator",
        action="rotate_secret",
        target="coinbase_key",
        result="success",
        pre_state={"api_key": "old-api-value", "nested": {"token": "old-token-value", "safe": "ok"}},
        post_state={"secret": "new-secret-value"},
        extra={"password_hint": "bad", "public_note": "kept"},
        event_id="redaction-test-event",
    )

    assert event["pre_state"]["api_key"] == "<redacted>"
    assert event["pre_state"]["nested"]["token"] == "<redacted>"
    assert event["pre_state"]["nested"]["safe"] == "ok"
    assert event["post_state"]["secret"] == "<redacted>"
    assert event["extra"]["password_hint"] == "<redacted>"
    assert event["extra"]["public_note"] == "kept"
    encoded = json.dumps(event)
    assert "old-api-value" not in encoded
    assert "old-token-value" not in encoded
    assert "new-secret-value" not in encoded


def test_operator_event_journal_rejects_missing_required_identity():
    with pytest.raises(OperatorEventJournalError, match="missing_required_field:actor"):
        build_operator_event(
            actor="",
            action="halt",
            target="live_trading",
            result="success",
        )


def test_operator_event_journal_write_failure_is_explicit(tmp_path):
    unwritable_target = tmp_path / "as_dir"
    unwritable_target.mkdir()

    with pytest.raises(OperatorEventJournalError, match="operator_event_write_failed"):
        append_operator_event(
            actor="operator",
            action="halt",
            target="live_trading",
            result="success",
            path=unwritable_target,
        )


def test_record_operator_event_cli_writes_jsonl(tmp_path, capsys):
    from scripts.record_operator_event import main
    import sys

    path = tmp_path / "events.jsonl"
    old_argv = sys.argv
    try:
        sys.argv = [
            "record_operator_event.py",
            "--actor",
            "operator",
            "--action",
            "note",
            "--target",
            "launch_packet",
            "--result",
            "recorded",
            "--reason",
            "manual_drill",
            "--extra-json",
            '{"api_token":"sensitive","safe":"ok"}',
            "--path",
            str(path),
        ]
        assert main() == 0
    finally:
        sys.argv = old_argv

    out = json.loads(capsys.readouterr().out)
    assert out["path"] == str(path)
    rows = load_operator_events(path)
    assert len(rows) == 1
    assert rows[0]["extra"]["api_token"] == "<redacted>"
    assert rows[0]["extra"]["safe"] == "ok"


def test_record_operator_event_script_bootstraps_when_run_as_file(tmp_path):
    path = tmp_path / "events.jsonl"

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/record_operator_event.py",
            "--actor",
            "operator",
            "--action",
            "note",
            "--target",
            "launch_packet",
            "--result",
            "recorded",
            "--reason",
            "direct_file_execution",
            "--path",
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert out["path"] == str(path)
    assert load_operator_events(path)[0]["reason"] == "direct_file_execution"
