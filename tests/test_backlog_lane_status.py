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


def test_backlog_lane_status_counts_lanes_and_preserves_hashes(tmp_path: Path) -> None:
    from services.analytics.backlog_lane_status import build_backlog_lane_status

    _write_lane_doc(tmp_path)
    (tmp_path / "REMAINING_TASKS.md").write_text("See docs/BACKLOG_EXECUTION_LANES.md", encoding="utf-8")

    out = build_backlog_lane_status(repo_root=tmp_path)

    assert out["ok"] is True
    assert out["read_only"] is True
    assert out["does_not_decide_backlog_items"] is True
    assert out["lane_count"] == 4
    assert out["total_item_count"] == 8
    assert out["source_doc_sha256"]
    assert out["backlog_sha256"]
    assert out["summary"]["high_risk_gate_execution_deploy"] == 2
    assert any("continues with detail" in item for row in out["lanes"] for item in row["items"])


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
        lambda repo_root=None: {
            "ok": True,
            "lane_count": 4,
            "total_item_count": 7,
            "summary": {
                "passive_operator_evidence": 1,
                "low_risk_docs_tests": 2,
                "medium_risk_runtime_read_only": 3,
                "high_risk_gate_execution_deploy": 1,
            },
            "lanes": [{"name": "Low-Risk Docs / Tests", "item_count": 2}],
            "missing_lanes": [],
        },
    )
    monkeypatch.setattr(script.sys, "argv", ["report_backlog_lane_status.py"])

    assert script.main() == 0
    out = capsys.readouterr().out
    assert "Backlog Lane Status" in out
    assert "low=2" in out
    assert "Low-Risk Docs / Tests: 2" in out
