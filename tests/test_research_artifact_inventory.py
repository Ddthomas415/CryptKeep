from __future__ import annotations

import json
from pathlib import Path


def _write_artifact(root: Path, rel: str, payload: dict) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_research_artifact_inventory_reports_latest_hash_and_missing_actions(tmp_path: Path) -> None:
    from services.analytics.research_artifact_inventory import build_research_artifact_inventory

    _write_artifact(
        tmp_path,
        ".cbp_state/data/research/price_action_pipeline/20260728T130459Z/pipeline_summary.json",
        {
            "report_type": "price_action_research_pipeline",
            "ok": True,
            "read_only": True,
            "generated_at": "2026-07-28T13:04:59+00:00",
        },
    )
    _write_artifact(
        tmp_path,
        ".cbp_state/data/research/price_action_pipeline/20260728T130459Z/context_labels.json",
        {
            "artifact_type": "price_action_context_labels_v1",
            "ok": True,
            "not_campaign_evidence": True,
            "not_promotion_evidence": True,
        },
    )

    out = build_research_artifact_inventory(repo_root=tmp_path, lane="price_action")
    rows = {row["artifact_id"]: row for row in out["artifacts"]}

    assert out["ok"] is True
    assert out["read_only"] is True
    assert out["does_not_run_research"] is True
    assert out["does_not_fetch_market_data"] is True
    assert out["does_not_mutate_state"] is True
    assert out["not_campaign_evidence"] is True
    assert out["not_promotion_evidence"] is True
    assert out["not_execution_input"] is True
    assert rows["price_action_pipeline_summary"]["latest_status"] == "latest_ok"
    assert rows["price_action_pipeline_summary"]["latest_sha256"]
    assert rows["price_action_pipeline_summary"]["latest_generated_at"] == "2026-07-28T13:04:59+00:00"
    assert rows["price_action_context_labels"]["boundary_flags"]["not_campaign_evidence"] is True
    assert rows["price_action_forward_returns"]["latest_status"] == "missing"
    assert rows["price_action_forward_returns"]["blocking_reason"] == "latest_artifact_missing"
    assert "make price-action-research-pipeline" in rows["price_action_forward_returns"]["next_action"]
    assert rows["price_action_forward_returns"]["producer_plan"] == {
        "make_target": "price-action-research-pipeline",
        "make_args_variable": "PRICE_ACTION_RESEARCH_PIPELINE_ARGS",
        "required_inputs": ["accepted OHLCV archive input", "output path"],
        "requires_accepted_inputs": True,
        "command_hint": 'make price-action-research-pipeline PRICE_ACTION_RESEARCH_PIPELINE_ARGS="<accepted inputs>"',
    }
    assert out["summary"]["found"] == 2
    assert out["summary"]["missing"] >= 1


def test_research_artifact_inventory_reports_unreadable_as_hard_failure(tmp_path: Path) -> None:
    from services.analytics.research_artifact_inventory import build_research_artifact_inventory

    path = tmp_path / ".cbp_state/data/research/funding_threshold_pipeline/run1/funding_threshold_sensitivity.json"
    path.parent.mkdir(parents=True)
    path.write_text("{not json", encoding="utf-8")

    out = build_research_artifact_inventory(repo_root=tmp_path, artifact_id="funding_threshold_sensitivity")

    assert out["ok"] is False
    assert out["artifact_count"] == 1
    row = out["artifacts"][0]
    assert row["latest_status"] == "unreadable"
    assert row["blocking_reason"] == "latest_artifact_unreadable"
    assert row["latest_sha256"]


def test_research_artifact_inventory_reports_marker_mismatch(tmp_path: Path) -> None:
    from services.analytics.research_artifact_inventory import build_research_artifact_inventory

    _write_artifact(
        tmp_path,
        ".cbp_state/data/research/funding_threshold_pipeline/run1/pipeline_summary.json",
        {"report_type": "wrong_report", "ok": True, "read_only": True},
    )

    out = build_research_artifact_inventory(repo_root=tmp_path, artifact_id="funding_threshold_pipeline_summary")
    row = out["artifacts"][0]

    assert out["ok"] is False
    assert row["latest_status"] == "latest_not_ok"
    assert row["blocking_reason"] == "unexpected_artifact_marker"
    assert row["observed_marker"] == "wrong_report"


def test_research_artifact_inventory_treats_archive_triage_no_candidates_as_terminal(tmp_path: Path) -> None:
    from services.analytics.research_artifact_inventory import build_research_artifact_inventory

    _write_artifact(
        tmp_path,
        ".cbp_state/data/research/archive_parameter_sweep_triage/run1/triage.json",
        {
            "artifact_type": "archive_parameter_sweep_triage_v1",
            "ok": False,
            "reason": "insufficient_review_candidates",
            "candidates": [{"variant_id": "variant_001", "status": "not_candidate"}],
            "review_candidates": [],
        },
    )

    out = build_research_artifact_inventory(repo_root=tmp_path, artifact_id="archive_parameter_sweep_triage")
    row = out["artifacts"][0]

    assert out["ok"] is True
    assert row["latest_status"] == "latest_terminal_no_candidates"
    assert row["latest_ok"] is False
    assert row["blocking_reason"] is None
    assert row["action_required"] is False
    assert row["next_action"] == "none"
    assert out["summary"]["terminal_no_candidates"] == 1
    assert out["summary"]["latest_not_ok"] == 0
    assert out["summary"]["action_required"] == 0


def test_research_artifact_inventory_still_fails_other_not_ok_artifacts(tmp_path: Path) -> None:
    from services.analytics.research_artifact_inventory import build_research_artifact_inventory

    _write_artifact(
        tmp_path,
        ".cbp_state/data/research/archive_parameter_sweep_triage/run1/triage.json",
        {
            "artifact_type": "archive_parameter_sweep_triage_v1",
            "ok": False,
            "reason": "source_artifact_missing",
            "candidates": [],
            "review_candidates": [],
        },
    )

    out = build_research_artifact_inventory(repo_root=tmp_path, artifact_id="archive_parameter_sweep_triage")
    row = out["artifacts"][0]

    assert out["ok"] is False
    assert row["latest_status"] == "latest_not_ok"
    assert row["blocking_reason"] == "latest_artifact_not_ok"
    assert row["action_required"] is True


def test_research_artifact_inventory_fails_closed_on_unknown_artifact_id(tmp_path: Path) -> None:
    from services.analytics.research_artifact_inventory import build_research_artifact_inventory

    out = build_research_artifact_inventory(repo_root=tmp_path, artifact_id="missing_artifact")

    assert out["ok"] is False
    assert out["reason"] == "invalid_artifact_id"
    assert out["artifact_id_filter"] == "missing_artifact"
    assert out["artifacts"] == []
    assert "price_action_pipeline_summary" in out["available_artifact_ids"]


def test_research_artifact_inventory_fails_closed_on_unknown_lane(tmp_path: Path) -> None:
    from services.analytics.research_artifact_inventory import build_research_artifact_inventory

    out = build_research_artifact_inventory(repo_root=tmp_path, lane="missing_lane")

    assert out["ok"] is False
    assert out["reason"] == "invalid_lane"
    assert out["lane_filter"] == "missing_lane"
    assert out["artifacts"] == []
    assert out["available_lanes"] == ["archive", "funding", "price_action"]


def test_research_artifact_inventory_cli_prints_next_action(monkeypatch, capsys) -> None:
    from scripts.research import report_research_artifact_inventory as script

    monkeypatch.setattr(
        script,
        "build_research_artifact_inventory",
        lambda repo_root=None, lane=None, artifact_id=None: {
            "ok": True,
            "lane_filter": lane,
            "artifact_id_filter": artifact_id,
            "artifact_count": 1,
            "summary": {
                "found": 0,
                "missing": 1,
                "latest_ok": 0,
                "latest_not_ok": 0,
                "unreadable": 0,
                "action_required": 1,
            },
            "artifacts": [
                {
                    "artifact_id": "price_action_forward_returns",
                    "latest_status": "missing",
                    "lane": "price_action",
                    "artifact_count": 0,
                    "latest_path": None,
                    "action_required": True,
                    "blocking_reason": "latest_artifact_missing",
                    "producer_plan": {
                        "command_hint": (
                            'make price-action-research-pipeline '
                            'PRICE_ACTION_RESEARCH_PIPELINE_ARGS="<accepted inputs>"'
                        ),
                        "required_inputs": ["accepted OHLCV archive input", "output path"],
                    },
                    "next_action": "run make price-action-research-pipeline with accepted research inputs",
                }
            ],
        },
    )

    assert script.main(["--lane", "price_action", "--artifact-id", "price_action_forward_returns"]) == 0
    out = capsys.readouterr().out
    assert "Research Artifact Inventory" in out
    assert "lane_filter=price_action" in out
    assert "artifact_id_filter=price_action_forward_returns" in out
    assert 'producer=make price-action-research-pipeline PRICE_ACTION_RESEARCH_PIPELINE_ARGS="<accepted inputs>"' in out
    assert "required_inputs=accepted OHLCV archive input,output path" in out
    assert "next_action=run make price-action-research-pipeline" in out


def test_research_artifact_inventory_cli_prints_available_lanes(monkeypatch, capsys) -> None:
    from scripts.research import report_research_artifact_inventory as script

    monkeypatch.setattr(
        script,
        "build_research_artifact_inventory",
        lambda repo_root=None, lane=None, artifact_id=None: {
            "ok": False,
            "reason": "invalid_lane",
            "lane_filter": lane,
            "artifact_id_filter": artifact_id,
            "available_lanes": ["archive", "funding", "price_action"],
            "artifact_count": 0,
            "summary": {
                "found": 0,
                "missing": 0,
                "latest_ok": 0,
                "latest_not_ok": 0,
                "unreadable": 0,
                "action_required": 0,
            },
            "artifacts": [],
        },
    )

    assert script.main(["--lane", "typo"]) == 2
    out = capsys.readouterr().out
    assert "reason=invalid_lane" in out
    assert "available_lanes=archive,funding,price_action" in out


def test_research_command_status_registers_artifact_inventory() -> None:
    from services.analytics.research_command_status import build_research_command_status

    out = build_research_command_status(command_id="research_artifact_inventory")

    assert out["ok"] is True
    assert out["command_count"] == 1
    row = out["commands"][0]
    assert row["script"] == "scripts/research/report_research_artifact_inventory.py"
    assert row["make_target"] == "research-artifact-inventory"
    assert row["lane"] == "status"
    assert row["input_class"] == "none"
