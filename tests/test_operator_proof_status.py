from __future__ import annotations

from pathlib import Path


def _write_docs(root: Path, *, include_passive: bool = True) -> None:
    docs = root / "docs"
    docs.mkdir()
    parts = ["# Backlog Execution Lanes", "", "## Current Backlog Lane Map", ""]
    if include_passive:
        parts.extend(
            [
                "### Passive / Operator Evidence",
                "",
                "- First host-side proof",
                "- Multi-line proof",
                "  continues with detail",
                "",
            ]
        )
    parts.extend(
        [
            "### Low-Risk Docs / Tests",
            "",
            "- Docs-only item",
            "",
        ]
    )
    (docs / "BACKLOG_EXECUTION_LANES.md").write_text("\n".join(parts), encoding="utf-8")


def test_operator_proof_status_reports_passive_items_and_markers(tmp_path: Path) -> None:
    from services.analytics.operator_proof_status import build_operator_proof_status

    _write_docs(tmp_path)
    (tmp_path / "REMAINING_TASKS.md").write_text(
        "\n".join(
            [
                "1. Item.",
                "   Remaining proof: run the host drill.",
                "   Remaining capped-live proof: venue time check.",
                "   Remaining coverage: no-secret scan.",
                "   2026-07-01: implementation is proof-ready for independent review.",
                "   host-side status still required.",
            ]
        ),
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is True
    assert out["read_only"] is True
    assert out["does_not_close_proof"] is True
    assert out["does_not_run_campaigns"] is True
    assert out["does_not_fetch_market_data"] is True
    assert out["does_not_mutate_state"] is True
    assert out["passive_operator_item_count"] == 2
    assert out["lane_doc_sha256"]
    assert out["backlog_sha256"]
    assert any("continues with detail" in row["text"] for row in out["passive_operator_items"])
    assert out["summary"]["remaining_proof_or_coverage_markers"] == 3
    assert out["summary"]["host_side_markers"] == 1
    assert out["summary"]["proof_ready_markers"] == 1
    categories = {row["category"] for row in out["proof_markers"]}
    assert "remaining_capped_live_proof" in categories
    assert "remaining_coverage" in categories


def test_operator_proof_status_fails_closed_without_passive_lane(tmp_path: Path) -> None:
    from services.analytics.operator_proof_status import build_operator_proof_status

    _write_docs(tmp_path, include_passive=False)
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is False
    assert out["passive_operator_item_count"] == 0


def test_report_operator_proof_status_cli(monkeypatch, capsys) -> None:
    from scripts import report_operator_proof_status as script

    monkeypatch.setattr(
        script,
        "build_operator_proof_status",
        lambda repo_root=None: {
            "ok": True,
            "passive_operator_item_count": 1,
            "proof_marker_count": 1,
            "summary": {
                "remaining_proof_or_coverage_markers": 1,
                "host_side_markers": 0,
                "proof_ready_markers": 0,
            },
            "passive_operator_items": [{"ordinal": 1, "text": "Run host proof"}],
            "proof_markers": [{"line": 7, "category": "remaining_proof", "text": "Remaining proof: run it"}],
        },
    )

    assert script.main([]) == 0
    out = capsys.readouterr().out
    assert "Operator Proof Status" in out
    assert "passive_items=1" in out
    assert "Run host proof" in out
    assert "L7 remaining_proof" in out
