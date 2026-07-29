from __future__ import annotations

from pathlib import Path


def _write_lane_doc(root: Path, *, omit_heading: str = "") -> None:
    docs = root / "docs"
    docs.mkdir()
    parts = ["# Backlog Execution Lanes", "", "## Current Backlog Lane Map", ""]
    lanes = (
        "Passive / Operator Evidence",
        "Low-Risk Docs / Tests",
        "Medium-Risk Runtime / Read-Only",
        "High-Risk Gate / Execution / Deploy",
    )
    for lane in lanes:
        if lane == omit_heading:
            continue
        parts.extend(
            [
                f"### {lane}",
                "",
                "- First item for " + lane,
                "- Multi-line item",
                "  continues with detail",
                "",
            ]
        )
    parts.extend(["## Batching Rule", "", "Batch only items from the same lane."])
    (docs / "BACKLOG_EXECUTION_LANES.md").write_text("\n".join(parts), encoding="utf-8")


def _write_lane_doc_with_examples(root: Path) -> None:
    docs = root / "docs"
    docs.mkdir()
    (docs / "BACKLOG_EXECUTION_LANES.md").write_text(
        "\n".join(
            [
                "# Backlog Execution Lanes",
                "",
                "## Current Backlog Lane Map",
                "",
                "### Passive / Operator Evidence",
                "",
                "- Host proof.",
                "",
                "### Low-Risk Docs / Tests",
                "",
                "These can be batched safely:",
                "",
                "- Actionable docs item.",
                "- Actionable guard item.",
                "",
                "Recent examples:",
                "",
                "- Completed parity guard.",
                "- Completed source-decision docs.",
                "",
                "### Medium-Risk Runtime / Read-Only",
                "",
                "- Read-only diagnostic.",
                "",
                "### High-Risk Gate / Execution / Deploy",
                "",
                "- Gate change.",
                "",
                "## Batching Rule",
                "",
                "Batch only items from the same lane.",
            ]
        ),
        encoding="utf-8",
    )


def test_backlog_lane_status_counts_lanes_and_preserves_hashes(tmp_path: Path) -> None:
    from services.analytics.backlog_lane_status import build_backlog_lane_status

    _write_lane_doc(tmp_path)
    (tmp_path / "REMAINING_TASKS.md").write_text("See docs/BACKLOG_EXECUTION_LANES.md", encoding="utf-8")

    out = build_backlog_lane_status(repo_root=tmp_path)

    assert out["ok"] is True
    assert out["read_only"] is True
    assert out["does_not_decide_backlog_items"] is True
    assert out["lane_filter"] is None
    assert out["lane_count"] == 4
    assert out["total_item_count"] == 8
    assert out["total_example_count"] == 0
    assert out["source_lane_count"] == 4
    assert out["source_total_item_count"] == 8
    assert out["source_total_example_count"] == 0
    assert out["source_doc_sha256"]
    assert out["backlog_sha256"]
    assert out["summary"]["high_risk_gate_execution_deploy"] == 2
    assert out["source_summary"]["high_risk_gate_execution_deploy"] == 2
    assert any("continues with detail" in item for row in out["lanes"] for item in row["items"])


def test_backlog_lane_status_separates_recent_examples_from_actionable_items(tmp_path: Path) -> None:
    from services.analytics.backlog_lane_status import build_backlog_lane_status

    _write_lane_doc_with_examples(tmp_path)
    (tmp_path / "REMAINING_TASKS.md").write_text("See docs/BACKLOG_EXECUTION_LANES.md", encoding="utf-8")

    out = build_backlog_lane_status(repo_root=tmp_path, lane="low_risk_docs_tests")

    assert out["ok"] is True
    assert out["total_item_count"] == 2
    assert out["total_example_count"] == 2
    lane = out["lanes"][0]
    assert lane["items"] == ["Actionable docs item.", "Actionable guard item."]
    assert lane["examples"] == ["Completed parity guard.", "Completed source-decision docs."]
    assert all("Completed" not in item for item in lane["items"])


def test_backlog_lane_status_filters_by_lane_key(tmp_path: Path) -> None:
    from services.analytics.backlog_lane_status import build_backlog_lane_status

    _write_lane_doc(tmp_path)
    (tmp_path / "REMAINING_TASKS.md").write_text("See docs/BACKLOG_EXECUTION_LANES.md", encoding="utf-8")

    out = build_backlog_lane_status(repo_root=tmp_path, lane="low_risk_docs_tests")

    assert out["ok"] is True
    assert out["lane_filter"] == "low_risk_docs_tests"
    assert out["lane_count"] == 1
    assert out["total_item_count"] == 2
    assert out["source_lane_count"] == 4
    assert out["source_total_item_count"] == 8
    assert out["lanes"][0]["name"] == "Low-Risk Docs / Tests"
    assert out["summary"]["low_risk_docs_tests"] == 2
    assert out["summary"]["high_risk_gate_execution_deploy"] == 0
    assert out["source_summary"]["high_risk_gate_execution_deploy"] == 2


def test_backlog_lane_status_rejects_unknown_lane(tmp_path: Path) -> None:
    from services.analytics.backlog_lane_status import build_backlog_lane_status

    _write_lane_doc(tmp_path)
    (tmp_path / "REMAINING_TASKS.md").write_text("See docs/BACKLOG_EXECUTION_LANES.md", encoding="utf-8")

    out = build_backlog_lane_status(repo_root=tmp_path, lane="execution")

    assert out["ok"] is False
    assert out["reason"] == "invalid_lane"
    assert out["lane_filter"] == "execution"
    assert out["lane_count"] == 0
    assert out["lanes"] == []
    assert "medium_risk_runtime_read_only" in out["available_lanes"]


def test_backlog_lane_status_fails_closed_when_lane_missing(tmp_path: Path) -> None:
    from services.analytics.backlog_lane_status import build_backlog_lane_status

    _write_lane_doc(tmp_path, omit_heading="High-Risk Gate / Execution / Deploy")
    (tmp_path / "REMAINING_TASKS.md").write_text("See docs/BACKLOG_EXECUTION_LANES.md", encoding="utf-8")

    out = build_backlog_lane_status(repo_root=tmp_path)

    assert out["ok"] is False
    assert out["missing_lanes"] == ["High-Risk Gate / Execution / Deploy"]


def test_backlog_lane_status_fails_closed_when_backlog_link_missing(tmp_path: Path) -> None:
    from services.analytics.backlog_lane_status import build_backlog_lane_status

    _write_lane_doc(tmp_path)
    (tmp_path / "REMAINING_TASKS.md").write_text("No lane-map link", encoding="utf-8")

    out = build_backlog_lane_status(repo_root=tmp_path)

    assert out["ok"] is False
    assert out["backlog_links_lane_doc"] is False


def test_report_backlog_lane_status_cli(monkeypatch, capsys) -> None:
    from scripts import report_backlog_lane_status as script

    monkeypatch.setattr(
        script,
        "build_backlog_lane_status",
        lambda repo_root=None, lane=None: {
            "ok": True,
            "lane_filter": lane,
            "source_lane_count": 4,
            "source_total_item_count": 7,
                "lane_count": 4,
                "total_item_count": 7,
                "total_example_count": 2,
                "summary": {
                    "passive_operator_evidence": 1,
                    "low_risk_docs_tests": 2,
                    "medium_risk_runtime_read_only": 3,
                    "high_risk_gate_execution_deploy": 1,
                },
                "lanes": [{"name": "Low-Risk Docs / Tests", "item_count": 2, "example_count": 2}],
                "missing_lanes": [],
                "source_total_example_count": 2,
            },
    )

    assert script.main(["--lane", "low_risk_docs_tests"]) == 0
    out = capsys.readouterr().out
    assert "Backlog Lane Status" in out
    assert "lane_filter=low_risk_docs_tests" in out
    assert "source_lanes=4 source_items=7 source_examples=2" in out
    assert "items=7 examples=2" in out
    assert "low=2" in out
    assert "Low-Risk Docs / Tests: 2 examples=2" in out
