from __future__ import annotations

from pathlib import Path


def _write_minimal_repo(root: Path) -> None:
    from services.analytics.research_command_status import RESEARCH_COMMANDS

    (root / "docs").mkdir()
    (root / "scripts" / "research").mkdir(parents=True)
    (root / "scripts" / "SCRIPTS.md").write_text(
        "\n".join(
            f"{spec.script.removeprefix('scripts/')} make {spec.make_target or '-'}"
            for spec in RESEARCH_COMMANDS
        ),
        encoding="utf-8",
    )
    for spec in RESEARCH_COMMANDS:
        path = root / spec.script
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
    (root / "Makefile").write_text(
        "\n".join(f"{spec.make_target}:\n\ttrue" for spec in RESEARCH_COMMANDS if spec.make_target),
        encoding="utf-8",
    )
    lanes = (
        "Passive / Operator Evidence",
        "Low-Risk Docs / Tests",
        "Medium-Risk Runtime / Read-Only",
        "High-Risk Gate / Execution / Deploy",
    )
    parts = ["# Backlog Execution Lanes", "", "## Current Backlog Lane Map", ""]
    for lane in lanes:
        parts.extend([f"### {lane}", "", f"- Item for {lane}", ""])
    (root / "docs" / "BACKLOG_EXECUTION_LANES.md").write_text("\n".join(parts), encoding="utf-8")
    (root / "REMAINING_TASKS.md").write_text(
        "See docs/BACKLOG_EXECUTION_LANES.md\nRemaining proof: run host drill.\nhost-side status required.",
        encoding="utf-8",
    )


def test_operator_status_bundle_combines_existing_status_reports(tmp_path: Path) -> None:
    from services.analytics.operator_status_bundle import build_operator_status_bundle

    _write_minimal_repo(tmp_path)

    out = build_operator_status_bundle(repo_root=tmp_path)

    assert out["ok"] is True
    assert out["read_only"] is True
    assert out["planning_only"] is True
    assert out["does_not_run_campaigns"] is True
    assert out["does_not_fetch_market_data"] is True
    assert out["does_not_mutate_state"] is True
    assert set(out["reports"]) == {
        "backlog_lane_status",
        "research_pipeline_status",
        "research_command_status",
        "operator_proof_status",
    }
    assert out["summary"]["passive_operator_items"] == 1
    assert out["summary"]["research_pipelines_wired"] == 2
    assert out["summary"]["research_pipelines_not_run"] == 2
    assert out["summary"]["research_pipeline_actions_required"] == 2
    assert len(out["actions"]["research_pipelines"]) == 2
    assert all(row["blocking_reason"] == "latest_summary_missing" for row in out["actions"]["research_pipelines"])
    assert out["summary"]["research_commands_wired"] >= 19
    assert out["summary"]["research_commands_not_wired"] == 0
    assert out["summary"]["remaining_proof_or_coverage_markers"] == 1
    assert out["summary"]["host_side_markers"] == 1


def test_report_operator_status_bundle_cli(monkeypatch, capsys) -> None:
    from scripts import report_operator_status_bundle as script

    monkeypatch.setattr(
        script,
        "build_operator_status_bundle",
        lambda repo_root=None: {
            "ok": True,
            "summary": {
                "passive_operator_items": 15,
                "low_risk_docs_tests": 13,
                "medium_risk_runtime_read_only": 7,
                "high_risk_gate_execution_deploy": 7,
                "research_pipelines_wired": 2,
                "research_pipelines_latest_ok": 0,
                "research_pipelines_not_run": 2,
                "research_pipeline_actions_required": 1,
                "research_commands_wired": 19,
                "research_commands_not_wired": 0,
                "remaining_proof_or_coverage_markers": 27,
                "host_side_markers": 17,
                "proof_ready_markers": 25,
            },
            "actions": {
                "research_pipelines": [
                    {
                        "pipeline_id": "price_action",
                        "latest_status": "not_run",
                        "blocking_reason": "latest_summary_missing",
                        "next_action": "run make price-action-research-pipeline with the required research inputs",
                    }
                ]
            },
        },
    )

    assert script.main([]) == 0
    out = capsys.readouterr().out
    assert "Operator Status Bundle" in out
    assert "passive=15" in out
    assert "wired=2" in out
    assert "actions_required=1" in out
    assert "research_action: price_action" in out
    assert "latest_summary_missing" in out
    assert "research_commands: wired=19" in out
    assert "remaining=27" in out
