from __future__ import annotations

from pathlib import Path


def _write_minimal_repo(root: Path, *, omit_command: str = "", omit_doc_link: str = "") -> None:
    (root / "docs" / "research").mkdir(parents=True)
    (root / "docs" / "work_log").mkdir(parents=True)
    required_docs = (
        "docs/CURRENT_SYSTEM_DIAGRAM.md",
        "REMAINING_TASKS.md",
        "docs/BACKLOG_EXECUTION_LANES.md",
        "docs/OPERATOR_GOVERNANCE_LANES.md",
        "docs/LAUNCH_CHECKLIST.md",
        "docs/research/strategy_expansion_roadmap.md",
        "docs/research/derivatives_intraday_roadmap.md",
        "docs/work_log/review_stabilized_work_log.md",
    )
    for rel in required_docs:
        (root / rel).write_text(f"{rel}\n", encoding="utf-8")
    (root / "REMAINING_TASKS.md").write_text(
        "docs/BACKLOG_EXECUTION_LANES.md\n"
        "docs/ROADMAP_TRACKING_CHECKLIST.md\n",
        encoding="utf-8",
    )
    (root / "docs" / "BACKLOG_EXECUTION_LANES.md").write_text(
        "docs/ROADMAP_TRACKING_CHECKLIST.md\n"
        "does not authorize runtime work\n",
        encoding="utf-8",
    )
    commands = (
        "make roadmap-tracking-status-json",
        "make operator-next-actions-json OPERATOR_NEXT_ACTIONS_MAX=20",
        "make operator-proof-status-json",
        "make operator-read-only-command-status-json",
        "make backlog-lane-status-json",
        "make status-paper-gate-velocity-json",
        "make status-paper-campaigns",
        "make check-cost-assumptions-json",
        "make check-edge-cadence-json",
        "make research-pipeline-status-json",
        "make research-command-status-json",
    )
    doc_lines = [
        "# CryptKeep Roadmap Tracking Checklist",
        "It does not replace `REMAINING_TASKS.md`",
        "This checklist does not authorize:",
        "live trading;",
        "Current operating phase: paper-evidence collection and read-only research.",
        "deterministic trading/risk engine remains the only authority",
        "Batch only items from the same lane.",
    ]
    doc_lines.extend(rel for rel in required_docs if rel != omit_doc_link)
    doc_lines.extend(command for command in commands if command != omit_command)
    (root / "docs" / "ROADMAP_TRACKING_CHECKLIST.md").write_text("\n".join(doc_lines), encoding="utf-8")
    make_targets = "\n".join(f"{command.split()[1]}:\n\t@true" for command in commands)
    (root / "Makefile").write_text(make_targets, encoding="utf-8")


def test_roadmap_tracking_status_reports_real_repo_ok() -> None:
    from services.analytics.roadmap_tracking_status import build_roadmap_tracking_status

    out = build_roadmap_tracking_status()

    assert out["ok"] is True
    assert out["read_only"] is True
    assert out["planning_only"] is True
    assert out["does_not_run_campaigns"] is True
    assert out["does_not_fetch_market_data"] is True
    assert out["does_not_mutate_state"] is True
    assert out["summary"]["source_doc_count"] == 8
    assert out["summary"]["command_count"] == 11
    assert out["summary"]["commands_listed"] == out["summary"]["command_count"]
    assert out["summary"]["boundaries_present"] == out["summary"]["boundary_count"]


def test_roadmap_tracking_status_fails_when_source_doc_not_linked(tmp_path: Path) -> None:
    from services.analytics.roadmap_tracking_status import build_roadmap_tracking_status

    _write_minimal_repo(tmp_path, omit_doc_link="docs/LAUNCH_CHECKLIST.md")

    out = build_roadmap_tracking_status(repo_root=tmp_path)

    assert out["ok"] is False
    assert out["reason"] == "roadmap_tracking_incomplete"
    assert out["unlinked_docs"] == ["docs/LAUNCH_CHECKLIST.md"]


def test_roadmap_tracking_status_fails_when_command_missing(tmp_path: Path) -> None:
    from services.analytics.roadmap_tracking_status import build_roadmap_tracking_status

    missing = "make status-paper-campaigns"
    _write_minimal_repo(tmp_path, omit_command=missing)

    out = build_roadmap_tracking_status(repo_root=tmp_path)

    assert out["ok"] is False
    assert out["missing_commands"] == [missing]


def test_roadmap_tracking_status_cli_json(capsys) -> None:
    from scripts import report_roadmap_tracking_status as script

    rc = script.main(["--json"])
    captured = capsys.readouterr()

    assert rc == 0
    assert '"report_type": "roadmap_tracking_status"' in captured.out
    assert '"ok": true' in captured.out
