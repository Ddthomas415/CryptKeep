from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from services.events.platform_event_journal import append_platform_event

ROOT = Path(__file__).resolve().parents[1]


def test_report_platform_event_journal_cli_reports_summary(tmp_path, capsys):
    from scripts.report_platform_event_journal import main

    path = tmp_path / "platform_events.jsonl"
    append_platform_event(event_type="EvidenceArtifactGenerated", producer="test", path=path)
    old_argv = sys.argv
    try:
        sys.argv = ["report_platform_event_journal.py", "--path", str(path)]
        assert main() == 0
    finally:
        sys.argv = old_argv

    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["event_count"] == 1
    assert out["event_types"] == {"EvidenceArtifactGenerated": 1}


def test_report_platform_event_journal_cli_returns_2_when_required_empty(tmp_path, capsys):
    from scripts.report_platform_event_journal import main

    path = tmp_path / "missing.jsonl"
    old_argv = sys.argv
    try:
        sys.argv = ["report_platform_event_journal.py", "--path", str(path), "--require-events"]
        assert main() == 2
    finally:
        sys.argv = old_argv

    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False
    assert out["reason"] == "platform_event_journal_empty"


def test_report_platform_event_journal_script_bootstraps_when_run_as_file(tmp_path):
    path = tmp_path / "platform_events.jsonl"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "report_platform_event_journal.py"),
            "--path",
            str(path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    out = json.loads(result.stdout)
    assert out["ok"] is True
    assert out["path"] == str(path)
