from __future__ import annotations

import json
import sys

from services.audit.operator_event_journal import append_operator_event
from services.audit.operator_event_replay import replay_live_arm_to_halt


def test_arm_to_halt_replay_passes_when_arm_precedes_halt(tmp_path):
    path = tmp_path / "operator_events.jsonl"
    append_operator_event(
        actor="operator",
        action="live_enable",
        target="live_trading",
        result="ok",
        reason="drill",
        post_state={"armed": True, "system_guard": {"state": "RUNNING"}},
        path=path,
    )
    append_operator_event(
        actor="operator",
        action="live_disable",
        target="live_trading",
        result="ok",
        reason="drill_halt",
        post_state={"system_guard": {"state": "HALTED"}, "kill_switch": {"armed": True}},
        path=path,
    )

    report = replay_live_arm_to_halt(path)

    assert report["ok"] is True
    assert report["reason"] == "ok"
    assert report["arm_event"]["action"] == "live_enable"
    assert report["halt_event"]["action"] == "live_disable"


def test_arm_to_halt_replay_reports_missing_arm_for_disable_only(tmp_path):
    path = tmp_path / "operator_events.jsonl"
    append_operator_event(
        actor="operator",
        action="live_disable",
        target="live_trading",
        result="ok",
        reason="drill_halt",
        post_state={"system_guard": {"state": "HALTED"}},
        path=path,
    )

    report = replay_live_arm_to_halt(path)

    assert report["ok"] is False
    assert report["reason"] == "missing_live_arm_event"
    assert report["halt_event"] is None


def test_arm_to_halt_replay_reports_missing_halt_after_arm(tmp_path):
    path = tmp_path / "operator_events.jsonl"
    append_operator_event(
        actor="operator",
        action="live_enable",
        target="live_trading",
        result="ok",
        reason="drill",
        post_state={"armed": True},
        path=path,
    )

    report = replay_live_arm_to_halt(path)

    assert report["ok"] is False
    assert report["reason"] == "missing_live_halt_event_after_arm"
    assert report["arm_event"]["action"] == "live_enable"


def test_arm_to_halt_replay_missing_journal_fails(tmp_path):
    report = replay_live_arm_to_halt(tmp_path / "missing.jsonl")

    assert report["ok"] is False
    assert report["reason"] == "operator_event_journal_missing"


def test_check_operator_arm_to_halt_replay_cli_writes_evidence(tmp_path, capsys):
    from scripts.check_operator_arm_to_halt_replay import main

    path = tmp_path / "operator_events.jsonl"
    evidence = tmp_path / "evidence"
    append_operator_event(
        actor="operator",
        action="live_enable",
        target="live_trading",
        result="ok",
        reason="drill",
        post_state={"armed": True},
        path=path,
    )
    append_operator_event(
        actor="operator",
        action="live_disable",
        target="live_trading",
        result="ok",
        reason="drill_halt",
        post_state={"status": {"system_guard": {"state": "HALTED"}}},
        path=path,
    )

    old_argv = sys.argv
    try:
        sys.argv = [
            "check_operator_arm_to_halt_replay.py",
            "--path",
            str(path),
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
    assert len(list(evidence.glob("operator-arm-to-halt-replay-*.json"))) == 1
