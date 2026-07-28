from __future__ import annotations

from pathlib import Path


def _write_minimal_repo(root: Path) -> None:
    (root / "docs").mkdir()
    (root / "scripts" / "research").mkdir(parents=True)
    (root / "scripts" / "SCRIPTS.md").write_text(
        "\n".join(
            [
                "research/run_price_action_research_pipeline.py make price-action-research-pipeline",
                "research/run_funding_threshold_research_pipeline.py make funding-threshold-research-pipeline",
            ]
        ),
        encoding="utf-8",
    )
    (root / "scripts" / "research" / "run_price_action_research_pipeline.py").write_text("", encoding="utf-8")
    (root / "scripts" / "research" / "run_funding_threshold_research_pipeline.py").write_text("", encoding="utf-8")
    (root / "Makefile").write_text(
        "price-action-research-pipeline:\n\ttrue\nfunding-threshold-research-pipeline:\n\ttrue\n",
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
        "operator_proof_status",
    }
    assert out["summary"]["passive_operator_items"] == 1
    assert out["summary"]["research_pipelines_wired"] == 2
    assert out["summary"]["research_pipelines_not_run"] == 2
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
                "remaining_proof_or_coverage_markers": 27,
                "host_side_markers": 17,
                "proof_ready_markers": 25,
            },
        },
    )

    assert script.main([]) == 0
    out = capsys.readouterr().out
    assert "Operator Status Bundle" in out
    assert "passive=15" in out
    assert "wired=2" in out
    assert "remaining=27" in out
