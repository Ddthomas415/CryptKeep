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
    assert out["section_filter"] is None
    assert out["shown_report_count"] == 4
    assert set(out["shown_sections"]) == {
        "backlog",
        "research_pipeline",
        "research_command",
        "operator_proof",
    }
    assert set(out["reports"]) == {
        "backlog_lane_status",
        "research_pipeline_status",
        "research_command_status",
        "operator_proof_status",
    }
    assert out["summary"]["passive_operator_items"] == 1
    assert out["summary"]["backlog_lane_actions_required"] == 0
    assert out["summary"]["passive_operator_evidence_actions_required"] == 1
    assert out["summary"]["research_pipelines_wired"] == 2
    assert out["summary"]["research_pipelines_not_run"] == 2
    assert out["summary"]["research_pipeline_actions_required"] == 2
    assert len(out["actions"]["research_pipelines"]) == 2
    assert all(row["blocking_reason"] == "latest_summary_missing" for row in out["actions"]["research_pipelines"])
    assert out["summary"]["research_commands_wired"] >= 19
    assert out["summary"]["research_commands_not_wired"] == 0
    assert out["summary"]["research_command_actions_required"] == 0
    assert out["summary"]["remaining_proof_or_coverage_markers"] == 1
    assert out["summary"]["host_side_markers"] == 1
    assert out["summary"]["operator_proof_actions_required"] >= 1
    assert out["actions"]["passive_operator_evidence"]
    assert out["actions"]["operator_proofs"]


def test_operator_status_bundle_filters_by_section(tmp_path: Path) -> None:
    from services.analytics.operator_status_bundle import build_operator_status_bundle

    _write_minimal_repo(tmp_path)

    out = build_operator_status_bundle(repo_root=tmp_path, section="research_pipeline")

    assert out["ok"] is True
    assert out["section_filter"] == "research_pipeline"
    assert out["shown_sections"] == ["research_pipeline"]
    assert out["source_report_count"] == 4
    assert out["shown_report_count"] == 1
    assert set(out["reports"]) == {"research_pipeline_status"}
    assert set(out["actions"]) == {"research_pipelines"}
    assert out["summary"]["research_pipelines_wired"] == 2
    assert out["shown_action_count"] == len(out["actions"]["research_pipelines"])


def test_operator_status_bundle_forwards_backlog_filter(tmp_path: Path) -> None:
    from services.analytics.operator_status_bundle import build_operator_status_bundle

    _write_minimal_repo(tmp_path)

    out = build_operator_status_bundle(
        repo_root=tmp_path,
        section="backlog",
        backlog_lane="low_risk_docs_tests",
    )

    assert out["ok"] is True
    assert out["section_filter"] == "backlog"
    assert out["backlog_lane_filter"] == "low_risk_docs_tests"
    assert out["reports"]["backlog_lane_status"]["lane_filter"] == "low_risk_docs_tests"
    assert out["summary"]["low_risk_docs_tests"] == 1
    assert out["summary"]["high_risk_gate_execution_deploy"] == 0
    assert out["shown_sections"] == ["backlog"]
    assert out["summary"]["backlog_lane_actions_required"] == 1
    assert set(out["actions"]) == {"backlog_lanes"}
    assert out["actions"]["backlog_lanes"] == [
        {
            "lane_key": "low_risk_docs_tests",
            "lane_name": "Low-Risk Docs / Tests",
            "ordinal": 1,
            "text": "Item for Low-Risk Docs / Tests",
            "next_action": "select or execute a scoped batch for Item for Low-Risk Docs / Tests",
        }
    ]


def test_operator_status_bundle_forwards_research_command_filters(tmp_path: Path) -> None:
    from services.analytics.operator_status_bundle import build_operator_status_bundle

    _write_minimal_repo(tmp_path)

    out = build_operator_status_bundle(
        repo_root=tmp_path,
        section="research_command",
        research_command_lane="funding",
        research_command_input_class="artifact_input",
    )

    report = out["reports"]["research_command_status"]
    assert out["ok"] is True
    assert out["section_filter"] == "research_command"
    assert out["research_command_lane_filter"] == "funding"
    assert out["research_command_input_class_filter"] == "artifact_input"
    assert report["lane_filter"] == "funding"
    assert report["input_class_filter"] == "artifact_input"
    assert out["summary"]["research_commands_wired"] == report["command_count"]
    assert out["shown_sections"] == ["research_command"]
    assert all(row["lane"] == "funding" for row in report["commands"])
    assert all(row["input_class"] == "artifact_input" for row in report["commands"])
    assert out["actions"]["research_commands"] == []


def test_operator_status_bundle_surfaces_research_command_actions(tmp_path: Path) -> None:
    from services.analytics.operator_status_bundle import build_operator_status_bundle
    from services.analytics.research_command_status import RESEARCH_COMMANDS

    _write_minimal_repo(tmp_path)
    missing = next(spec for spec in RESEARCH_COMMANDS if spec.command_id == "funding_threshold_pipeline")
    (tmp_path / missing.script).unlink()

    out = build_operator_status_bundle(
        repo_root=tmp_path,
        section="research_command",
        research_command_lane="funding",
    )

    assert out["ok"] is False
    assert out["summary"]["research_commands_not_wired"] == 1
    assert out["summary"]["research_command_actions_required"] == 1
    assert out["shown_sections"] == ["research_command"]
    assert set(out["actions"]) == {"research_commands"}
    assert out["shown_action_count"] == 1
    assert out["actions"]["research_commands"] == [
        {
            "command_id": "funding_threshold_pipeline",
            "lane": "funding",
            "input_class": "state_input",
            "make_target": "funding-threshold-research-pipeline",
            "blocking_reason": "script_missing",
            "next_action": "repair research command wiring for funding_threshold_pipeline: script_missing",
        }
    ]


def test_operator_status_bundle_forwards_research_pipeline_filter(tmp_path: Path) -> None:
    from services.analytics.operator_status_bundle import build_operator_status_bundle

    _write_minimal_repo(tmp_path)

    out = build_operator_status_bundle(
        repo_root=tmp_path,
        section="research_pipeline",
        research_pipeline="price_action",
    )

    report = out["reports"]["research_pipeline_status"]
    assert out["ok"] is True
    assert out["section_filter"] == "research_pipeline"
    assert out["research_pipeline_filter"] == "price_action"
    assert report["pipeline_filter"] == "price_action"
    assert out["summary"]["research_pipelines_wired"] == report["pipeline_count"]
    assert out["shown_sections"] == ["research_pipeline"]
    assert all(row["pipeline_id"] == "price_action" for row in report["pipelines"])


def test_operator_status_bundle_forwards_proof_category(tmp_path: Path) -> None:
    from services.analytics.operator_status_bundle import build_operator_status_bundle

    _write_minimal_repo(tmp_path)

    out = build_operator_status_bundle(
        repo_root=tmp_path,
        section="operator_proof",
        operator_proof_category="host_side_reference",
    )

    report = out["reports"]["operator_proof_status"]
    assert out["ok"] is True
    assert out["section_filter"] == "operator_proof"
    assert out["operator_proof_category_filter"] == "host_side_reference"
    assert report["category_filter"] == "host_side_reference"
    assert out["shown_sections"] == ["operator_proof"]
    assert "passive_operator_evidence" in out["actions"]
    assert all(row["category"] == "host_side_reference" for row in report["proof_markers"])
    assert all(row["category"] == "host_side_reference" for row in out["actions"]["operator_proofs"])


def test_operator_status_bundle_forwards_proof_line(tmp_path: Path) -> None:
    from services.analytics.operator_status_bundle import build_operator_status_bundle

    _write_minimal_repo(tmp_path)

    out = build_operator_status_bundle(
        repo_root=tmp_path,
        section="operator_proof",
        operator_proof_line=3,
    )

    report = out["reports"]["operator_proof_status"]
    assert out["ok"] is True
    assert out["section_filter"] == "operator_proof"
    assert out["operator_proof_line_filter"] == 3
    assert report["line_filter"] == 3
    assert out["shown_sections"] == ["operator_proof"]
    assert "passive_operator_evidence" in out["actions"]
    assert all(row["line"] == 3 for row in report["proof_markers"])
    assert all(row["line"] == 3 for row in out["actions"]["operator_proofs"])


def test_operator_status_bundle_rejects_unknown_section(tmp_path: Path) -> None:
    from services.analytics.operator_status_bundle import build_operator_status_bundle

    _write_minimal_repo(tmp_path)

    out = build_operator_status_bundle(repo_root=tmp_path, section="execution")

    assert out["ok"] is False
    assert out["reason"] == "invalid_section"
    assert out["section_filter"] == "execution"
    assert out["shown_sections"] == []
    assert out["reports"] == {}
    assert out["actions"] == {}
    assert "research_pipeline" in out["available_sections"]


def test_report_operator_status_bundle_cli(monkeypatch, capsys) -> None:
    from scripts import report_operator_status_bundle as script

    monkeypatch.setattr(
        script,
        "build_operator_status_bundle",
        lambda repo_root=None, section=None, **filters: {
            "ok": True,
            "section_filter": section,
            "backlog_lane_filter": filters.get("backlog_lane"),
            "research_pipeline_filter": filters.get("research_pipeline"),
            "research_command_lane_filter": filters.get("research_command_lane"),
            "research_command_input_class_filter": filters.get("research_command_input_class"),
            "operator_proof_category_filter": filters.get("operator_proof_category"),
            "operator_proof_line_filter": int(filters.get("operator_proof_line") or 0) or None,
            "shown_sections": [section] if section else ["backlog", "research_pipeline", "operator_proof"],
            "summary": {
                "passive_operator_items": 15,
                "backlog_lane_actions_required": 1,
                "low_risk_docs_tests": 13,
                "medium_risk_runtime_read_only": 7,
                "high_risk_gate_execution_deploy": 7,
                "research_pipelines_wired": 2,
                "research_pipelines_latest_ok": 0,
                "research_pipelines_not_run": 2,
                "research_pipeline_actions_required": 1,
                "research_commands_wired": 19,
                "research_commands_not_wired": 0,
                "research_command_actions_required": 1,
                "remaining_proof_or_coverage_markers": 27,
                "host_side_markers": 17,
                "proof_ready_markers": 25,
                "operator_proof_actions_required": 2,
            },
            "reports": {
                "backlog_lane_status": {},
                "research_pipeline_status": {},
                "research_command_status": {},
                "operator_proof_status": {},
            },
            "actions": {
                "backlog_lanes": [
                    {
                        "ordinal": 1,
                        "lane_key": "low_risk_docs_tests",
                        "next_action": "select or execute a scoped batch",
                    }
                ],
                "research_pipelines": [
                    {
                        "pipeline_id": "price_action",
                        "latest_status": "not_run",
                        "blocking_reason": "latest_summary_missing",
                        "next_action": "run make price-action-research-pipeline with the required research inputs",
                    }
                ],
                "research_commands": [
                    {
                        "command_id": "funding_threshold_pipeline",
                        "lane": "funding",
                        "blocking_reason": "script_missing",
                        "next_action": "repair research command wiring for funding_threshold_pipeline: script_missing",
                    }
                ],
                "passive_operator_evidence": [
                    {
                        "ordinal": 1,
                        "next_action": "collect or record operator evidence: Run host proof",
                    }
                ],
                "operator_proofs": [
                    {
                        "line": 7,
                        "category": "remaining_proof",
                        "next_action": "produce or record the remaining proof referenced at REMAINING_TASKS.md:L7",
                    }
                ],
            },
        },
    )

    assert script.main(
        [
            "--section",
            "operator_proof",
            "--operator-proof-category",
            "host_side_reference",
            "--operator-proof-line",
            "7",
        ]
    ) == 0
    out = capsys.readouterr().out
    assert "Operator Status Bundle" in out
    assert "section_filter=operator_proof" in out
    assert "operator_proof_category_filter=host_side_reference" in out
    assert "operator_proof_line_filter=7" in out
    assert "passive=15" in out
    assert "backlog_action: #1 low_risk_docs_tests" in out
    assert "wired=2" in out
    assert "actions_required=1" in out
    assert "research_action: price_action" in out
    assert "latest_summary_missing" in out
    assert "research_commands: wired=19" in out
    assert "actions_required=1" in out
    assert "research_command_action: funding_threshold_pipeline" in out
    assert "remaining=27" in out
    assert "passive_action: #1" in out
    assert "collect or record operator evidence" in out
    assert "proof_action: L7 remaining_proof" in out
