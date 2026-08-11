from __future__ import annotations

import json
import sys

from services.audit.backup_artifact_secret_scan import scan_backup_artifact


def test_backup_artifact_secret_scan_passes_clean_backup(tmp_path):
    backup = tmp_path / "backup"
    state = backup / "state"
    state.mkdir(parents=True)
    (backup / "backup_manifest.json").write_text(
        json.dumps({"manifest_version": 1, "files": [{"rel": "state/safe.json"}]}),
        encoding="utf-8",
    )
    (state / "safe.json").write_text(json.dumps({"api_key": "<redacted>", "safe": "ok"}), encoding="utf-8")

    report = scan_backup_artifact(backup)

    assert report["ok"] is True
    assert report["finding_count"] == 0
    assert report["manifest_exists"] is True
    assert report["files_scanned"] == 2


def test_backup_artifact_secret_scan_flags_json_sensitive_key_without_value(tmp_path):
    backup = tmp_path / "backup"
    state = backup / "state"
    state.mkdir(parents=True)
    (backup / "backup_manifest.json").write_text("{}", encoding="utf-8")
    secret_value = "should-not-print"
    (state / "unsafe.json").write_text(json.dumps({"nested": {"api_token": secret_value}}), encoding="utf-8")

    report = scan_backup_artifact(backup)

    assert report["ok"] is False
    assert report["finding_count"] == 1
    finding = report["findings"][0]
    assert finding["path"] == "state/unsafe.json"
    assert finding["reason"] == "sensitive_key_unredacted"
    assert finding["json_path"] == "nested.api_token"
    assert finding["value"] == {"type": "str", "length": len(secret_value)}
    assert secret_value not in json.dumps(report)


def test_backup_artifact_secret_scan_flags_high_confidence_binary_patterns(tmp_path):
    backup = tmp_path / "backup"
    state = backup / "state"
    state.mkdir(parents=True)
    (backup / "backup_manifest.json").write_text("{}", encoding="utf-8")
    (state / "blob.sqlite").write_bytes(b"prefix github_pat_abcdefghijklmnopqrstuvwxyz123456 suffix")

    report = scan_backup_artifact(backup)

    assert report["ok"] is False
    assert report["findings"][0]["path"] == "state/blob.sqlite"
    assert report["findings"][0]["reason"] == "github_fine_grained_token"
    assert "github_pat_" not in json.dumps(report)


def test_backup_artifact_secret_scan_fails_missing_manifest(tmp_path):
    backup = tmp_path / "backup"
    backup.mkdir()

    report = scan_backup_artifact(backup)

    assert report["ok"] is False
    assert report["findings"][0]["reason"] == "backup_manifest_missing"


def test_check_backup_artifact_secrets_cli_writes_evidence_and_event(tmp_path, monkeypatch, capsys):
    from scripts.check_backup_artifact_secrets import main

    backup = tmp_path / "backup"
    state = backup / "state"
    state.mkdir(parents=True)
    (backup / "backup_manifest.json").write_text("{}", encoding="utf-8")
    (state / "safe.json").write_text(json.dumps({"token": "<redacted>"}), encoding="utf-8")
    evidence = tmp_path / "evidence"
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path / "state_root"))

    old_argv = sys.argv
    try:
        sys.argv = [
            "check_backup_artifact_secrets.py",
            str(backup),
            "--evidence-dest",
            str(evidence),
            "--json",
        ]
        assert main() == 0
    finally:
        sys.argv = old_argv

    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["evidence_path"].startswith(str(evidence))
    assert out["operator_event"]["ok"] is True
    journal = tmp_path / "state_root" / "data" / "operator_events" / "operator_events.jsonl"
    assert "state_backup_secret_scan" in journal.read_text(encoding="utf-8")
