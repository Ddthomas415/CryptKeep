from __future__ import annotations

import json
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
    assert all(row["action_required"] is True for row in out["passive_operator_items"])
    assert all("collect or record operator evidence" in row["next_action"] for row in out["passive_operator_items"])
    assert out["summary"]["remaining_proof_or_coverage_markers"] == 3
    assert out["summary"]["host_side_markers"] == 1
    assert out["summary"]["proof_ready_markers"] == 1
    categories = {row["category"] for row in out["proof_markers"]}
    assert "remaining_capped_live_proof" in categories
    assert "remaining_coverage" in categories
    assert all(row["action_required"] is True for row in out["proof_markers"])
    assert all("REMAINING_TASKS.md:L" in row["next_action"] for row in out["proof_markers"])


def test_operator_proof_status_fails_closed_without_passive_lane(tmp_path: Path) -> None:
    from services.analytics.operator_proof_status import build_operator_proof_status

    _write_docs(tmp_path, include_passive=False)
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is False
    assert out["passive_operator_item_count"] == 0


def test_operator_proof_status_filters_proof_markers_by_category(tmp_path: Path) -> None:
    from services.analytics.operator_proof_status import build_operator_proof_status

    _write_docs(tmp_path)
    (tmp_path / "REMAINING_TASKS.md").write_text(
        "\n".join(
            [
                "1. Item.",
                "   Remaining proof: run the host drill.",
                "   Remaining capped-live proof: venue time check.",
                "   2026-07-01: implementation is proof-ready for independent review.",
                "   host-side status still required.",
            ]
        ),
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path, category="host_side_reference")

    assert out["category_filter"] == "host_side_reference"
    assert out["passive_operator_item_count"] == 2
    assert out["proof_marker_count"] == 1
    assert out["source_proof_marker_count"] == 4
    assert out["summary"]["category_counts"] == {"host_side_reference": 1}
    assert out["summary"]["source_category_counts"]["proof_ready_implementation"] == 1
    assert [row["category"] for row in out["proof_markers"]] == ["host_side_reference"]


def test_operator_proof_status_classifies_host_side_remaining_proof_as_host_reference(
    tmp_path: Path,
) -> None:
    from services.analytics.operator_proof_status import build_operator_proof_status

    _write_docs(tmp_path)
    (tmp_path / "REMAINING_TASKS.md").write_text(
        "\n".join(
            [
                "1. Restore.",
                "   Remaining proof: host-side restore drill and migration packet.",
                "2. Promotion.",
                "   Remaining proof: promotion audit-write fail-closed policy and host-side promotion proof.",
                "3. Local.",
                "   Remaining proof: execute the local invariant check.",
            ]
        ),
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is True
    assert out["proof_marker_count"] == 3
    assert out["summary"]["category_counts"] == {
        "host_side_reference": 2,
        "remaining_proof": 1,
    }
    rows = {row["line"]: row for row in out["proof_markers"]}
    assert rows[2]["category"] == "host_side_reference"
    assert rows[4]["category"] == "host_side_reference"
    assert rows[6]["category"] == "remaining_proof"


def test_operator_proof_status_does_not_reopen_recorded_host_proof(tmp_path: Path) -> None:
    from services.analytics.operator_proof_status import build_operator_proof_status

    _write_docs(tmp_path)
    (tmp_path / "REMAINING_TASKS.md").write_text(
        "\n".join(
                [
                    "1. Item.",
                    "   2026-07-18 host proof recorded in docs/checkpoints/example.md:",
                    "   host-side checker returned ok=true.",
                    "   Host-side installation remains open: install the next timer.",
                ]
            ),
            encoding="utf-8",
        )

    out = build_operator_proof_status(repo_root=tmp_path, category="host_side_reference")

    assert out["ok"] is True
    assert out["proof_marker_count"] == 3
    assert out["summary"]["host_side_markers"] == 3
    assert out["summary"]["proof_markers_satisfied"] == 2
    assert out["summary"]["proof_marker_actions_required"] == 1
    assert out["summary"]["proof_markers_context_only"] == 0
    rows = {row["line"]: row for row in out["proof_markers"]}
    assert rows[2]["status"] == "satisfied_recorded"
    assert rows[2]["satisfied"] is True
    assert rows[2]["action_required"] is False
    assert rows[2]["next_action"] == "none"
    assert rows[3]["status"] == "satisfied_recorded"
    assert rows[3]["satisfied"] is True
    assert rows[3]["action_required"] is False
    assert rows[3]["next_action"] == "none"
    assert rows[4]["status"] == "open"
    assert rows[4]["satisfied"] is False
    assert rows[4]["action_required"] is True
    assert "host-side evidence" in rows[4]["next_action"]


def test_operator_proof_status_closes_recorded_crypto_edge_remaining_proof(
    tmp_path: Path,
) -> None:
    from services.analytics.operator_proof_status import build_operator_proof_status

    _write_docs(tmp_path)
    (tmp_path / "REMAINING_TASKS.md").write_text(
        "\n".join(
            [
                "14. Start scheduled read-only crypto-edge collection.",
                "    Remaining proof: operator-host schedule, recent OKX snapshot timestamps, cadence-gap alerting, and downstream context strategy/provenance review.",
                "    2026-07-12: crypto-edge paper qualification extension is ready for independent review.",
                "    2026-07-18: independently reviewed and accepted by the operator.",
                "    2026-07-18 final host proof recorded in docs/checkpoints/ready.md:",
                "    check_edge_cadence.py --json reports fresh OKX funding, open-interest, and basis snapshots with missing=[], stale=[].",
                "    This closes the host-side crypto-edge schedule/cadence proof.",
                "15. Another item.",
                "    Remaining proof: execute the next drill.",
            ]
        ),
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path, category="remaining_proof")

    assert out["ok"] is True
    assert out["proof_marker_count"] == 2
    assert out["summary"]["proof_markers_satisfied"] == 1
    assert out["summary"]["proof_marker_actions_required"] == 1
    rows = {row["line"]: row for row in out["proof_markers"]}
    assert rows[2]["status"] == "satisfied_recorded"
    assert rows[2]["action_required"] is False
    assert rows[2]["next_action"] == "none"
    assert rows[9]["status"] == "open"
    assert rows[9]["action_required"] is True


def test_operator_proof_status_keeps_crypto_edge_remaining_proof_open_without_final_host_proof(
    tmp_path: Path,
) -> None:
    from services.analytics.operator_proof_status import build_operator_proof_status

    _write_docs(tmp_path)
    (tmp_path / "REMAINING_TASKS.md").write_text(
        "\n".join(
            [
                "14. Start scheduled read-only crypto-edge collection.",
                "    Remaining proof: operator-host schedule, recent OKX snapshot timestamps, cadence-gap alerting, and downstream context strategy/provenance review.",
                "    2026-07-12: crypto-edge paper qualification extension is ready for independent review.",
                "    2026-07-18: independently reviewed and accepted by the operator.",
                "    The host-side crypto-edge schedule/cadence proof remains open.",
            ]
        ),
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path, category="remaining_proof")

    assert out["ok"] is True
    assert out["proof_marker_count"] == 1
    row = out["proof_markers"][0]
    assert row["status"] == "open"
    assert row["action_required"] is True


def test_operator_proof_status_does_not_treat_policy_mentions_as_proof_ready_actions(
    tmp_path: Path,
) -> None:
    from services.analytics.operator_proof_status import build_operator_proof_status

    _write_docs(tmp_path)
    (tmp_path / "REMAINING_TASKS.md").write_text(
        "\n".join(
            [
                "1. Item.",
                "   2026-07-13 real slice is proof-ready for independent review.",
                "   2026-07-21 refreshed lanes distinguish completed/proof-ready implementation text.",
                "   The warning not to rebuild completed/proof-ready work is policy text.",
            ]
        ),
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path, category="proof_ready_implementation")

    assert out["ok"] is True
    assert out["proof_marker_count"] == 3
    assert out["summary"]["proof_ready_markers"] == 3
    assert out["summary"]["proof_marker_actions_required"] == 1
    assert out["summary"]["proof_markers_context_only"] == 2
    rows = {row["line"]: row for row in out["proof_markers"]}
    assert rows[2]["status"] == "open"
    assert rows[2]["action_required"] is True
    assert rows[3]["status"] == "context_only"
    assert rows[3]["action_required"] is False
    assert rows[3]["next_action"] == "none"
    assert rows[4]["status"] == "context_only"
    assert rows[4]["action_required"] is False
    assert rows[4]["next_action"] == "none"


def test_operator_proof_status_rejects_unknown_category_filter(tmp_path: Path) -> None:
    from services.analytics.operator_proof_status import build_operator_proof_status

    _write_docs(tmp_path)
    (tmp_path / "REMAINING_TASKS.md").write_text(
        "\n".join(
            [
                "1. Item.",
                "   Remaining proof: run the host drill.",
                "   host-side status still required.",
            ]
        ),
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path, category="missing_category")

    assert out["ok"] is False
    assert out["reason"] == "invalid_category"
    assert out["category_filter"] == "missing_category"
    assert out["proof_marker_count"] == 0
    assert out["source_proof_marker_count"] == 2
    assert out["proof_markers"] == []
    assert out["available_categories"] == ["host_side_reference", "remaining_proof"]


def test_operator_proof_status_filters_proof_markers_by_line(tmp_path: Path) -> None:
    from services.analytics.operator_proof_status import build_operator_proof_status

    _write_docs(tmp_path)
    (tmp_path / "REMAINING_TASKS.md").write_text(
        "\n".join(
            [
                "1. Item.",
                "   Remaining proof: run the host drill.",
                "   host-side status still required.",
            ]
        ),
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path, line=3)

    assert out["ok"] is True
    assert out["line_filter"] == 3
    assert out["proof_marker_count"] == 1
    assert out["source_proof_marker_count"] == 2
    assert [row["line"] for row in out["proof_markers"]] == [3]
    assert [row["category"] for row in out["proof_markers"]] == ["host_side_reference"]


def test_operator_proof_status_rejects_invalid_line_filter(tmp_path: Path) -> None:
    from services.analytics.operator_proof_status import build_operator_proof_status

    _write_docs(tmp_path)
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")

    out = build_operator_proof_status(repo_root=tmp_path, line="abc")

    assert out["ok"] is False
    assert out["reason"] == "invalid_line"
    assert out["line_filter"] is None


def test_operator_proof_status_filters_passive_items_by_ordinal(tmp_path: Path) -> None:
    from services.analytics.operator_proof_status import build_operator_proof_status

    _write_docs(tmp_path)
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")

    out = build_operator_proof_status(repo_root=tmp_path, passive_ordinal=2)

    assert out["ok"] is True
    assert out["passive_operator_ordinal_filter"] == 2
    assert out["source_passive_operator_item_count"] == 2
    assert out["passive_operator_item_count"] == 1
    assert out["summary"]["passive_operator_items"] == 1
    assert out["summary"]["source_passive_operator_items"] == 2
    assert [row["ordinal"] for row in out["passive_operator_items"]] == [2]
    assert "continues with detail" in out["passive_operator_items"][0]["text"]
    assert out["proof_marker_scope"] == "suppressed_by_passive_ordinal"
    assert out["proof_marker_count"] == 0
    assert out["source_proof_marker_count"] == 1
    assert out["proof_markers"] == []
    assert out["summary"]["remaining_proof_or_coverage_markers"] == 0
    assert out["summary"]["source_category_counts"] == {"remaining_proof": 1}


def test_operator_proof_status_passive_ordinal_keeps_explicit_proof_filter(tmp_path: Path) -> None:
    from services.analytics.operator_proof_status import build_operator_proof_status

    _write_docs(tmp_path)
    (tmp_path / "REMAINING_TASKS.md").write_text(
        "\n".join(
            [
                "Remaining proof: run drill.",
                "host-side status still required.",
            ]
        ),
        encoding="utf-8",
    )

    out = build_operator_proof_status(
        repo_root=tmp_path,
        passive_ordinal=2,
        category="host_side_reference",
    )

    assert out["ok"] is True
    assert out["passive_operator_item_count"] == 1
    assert out["proof_marker_scope"] == "category"
    assert out["proof_marker_count"] == 1
    assert out["source_proof_marker_count"] == 2
    assert [row["category"] for row in out["proof_markers"]] == ["host_side_reference"]


def test_operator_proof_status_rejects_invalid_passive_ordinal(tmp_path: Path) -> None:
    from services.analytics.operator_proof_status import build_operator_proof_status

    _write_docs(tmp_path)
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")

    out = build_operator_proof_status(repo_root=tmp_path, passive_ordinal=99)

    assert out["ok"] is False
    assert out["reason"] == "invalid_passive_operator_ordinal"
    assert out["passive_operator_ordinal_filter"] is None
    assert out["passive_operator_items"] == []
    assert out["proof_marker_scope"] == "suppressed_by_passive_ordinal"
    assert out["proof_marker_count"] == 0
    assert out["source_proof_marker_count"] == 1
    assert out["proof_markers"] == []


def test_operator_proof_status_marks_pullback_stage0_passive_item_satisfied(tmp_path: Path) -> None:
    from services.analytics.operator_proof_status import build_operator_proof_status

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "BACKLOG_EXECUTION_LANES.md").write_text(
        "\n".join(
            [
                "# Backlog Execution Lanes",
                "",
                "### Passive / Operator Evidence",
                "",
                "- Pullback Stage 0 long proof if it is not already captured by the latest operator artifact.",
                "- Another host proof.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")
    artifact_dir = tmp_path / ".cbp_state" / "data" / "pullback_stage0_verification"
    artifact_dir.mkdir(parents=True)
    artifact = artifact_dir / "pullback_stage0_verification.latest.json"
    artifact.write_text(
        json.dumps(
            {
                "report_type": "pullback_stage0_verification",
                "status": "passed",
                "read_only": True,
                "strategy": "pullback_recovery",
                "session_strategy_id": "pullback_recovery_default",
                "blocking_checks": 0,
            }
        ),
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is True
    assert out["passive_operator_item_count"] == 2
    assert out["summary"]["passive_operator_items_satisfied"] == 1
    pullback = out["passive_operator_items"][0]
    assert pullback["action_required"] is False
    assert pullback["next_action"] == "none"
    assert pullback["artifact_status"]["artifact_id"] == "pullback_stage0_verification"
    assert pullback["artifact_status"]["artifact_exists"] is True
    assert pullback["artifact_status"]["satisfied"] is True
    assert out["passive_operator_items"][1]["action_required"] is True


def test_operator_proof_status_marks_paper_gate_velocity_passive_item_satisfied(tmp_path: Path) -> None:
    from services.analytics.operator_proof_status import build_operator_proof_status

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "BACKLOG_EXECUTION_LANES.md").write_text(
        "\n".join(
            [
                "# Backlog Execution Lanes",
                "",
                "### Passive / Operator Evidence",
                "",
                "- Canonical `es_daily_trend_v1` qualified round-trip collection and fresh paper-gate output.",
                "- Another host proof.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")
    artifact_dir = tmp_path / ".cbp_state" / "data" / "paper_gate_velocity"
    artifact_dir.mkdir(parents=True)
    artifact = artifact_dir / "paper_gate_velocity.latest.json"
    artifact.write_text(
        json.dumps(
            {
                "ok": True,
                "read_only": True,
                "report_type": "paper_gate_velocity",
                "generated_at": "2026-08-08T00:00:00+00:00",
                "strategy_id": "es_daily_trend_v1",
                "round_trips": {"qualified": 3, "required": 5, "remaining": 2},
                "qualified_bars": {"recorded": 47, "required": 60, "remaining": 13},
            }
        ),
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is True
    assert out["passive_operator_item_count"] == 2
    assert out["summary"]["passive_operator_items_satisfied"] == 1
    paper_gate = out["passive_operator_items"][0]
    assert paper_gate["action_required"] is False
    assert paper_gate["next_action"] == "none"
    assert paper_gate["artifact_status"]["artifact_id"] == "paper_gate_velocity"
    assert paper_gate["artifact_status"]["artifact_status"] == "recorded"
    assert paper_gate["artifact_status"]["satisfied"] is True
    assert out["passive_operator_items"][1]["action_required"] is True


def test_operator_proof_status_marks_cost_assumption_operational_markers_satisfied(tmp_path: Path) -> None:
    from services.analytics.operator_proof_status import build_operator_proof_status

    _write_docs(tmp_path)
    (tmp_path / "REMAINING_TASKS.md").write_text(
        "\n".join(
            [
                "1. Paper PnL.",
                "   Remaining operational proof: verify active campaign config uses realistic fee/slippage values.",
                "   Remaining operational proof: verify host fee/slippage values and use report fields to segment old evidence.",
                "   Remaining proof: unrelated drill.",
            ]
        ),
        encoding="utf-8",
    )
    artifact_dir = tmp_path / ".cbp_state" / "data" / "cost_assumptions"
    artifact_dir.mkdir(parents=True)
    artifact = artifact_dir / "cost_assumptions.latest.json"
    artifact.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "report_type": "cost_assumptions",
                "generated_at": "2026-08-08T00:00:00+00:00",
                "read_only": True,
                "overall": "warning",
                "checks": [{"name": "engine_costs_configured", "status": "warning"}],
            }
        ),
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path, category="remaining_operational_proof")

    assert out["ok"] is True
    assert out["proof_marker_count"] == 2
    assert out["summary"]["proof_marker_actions_required"] == 0
    assert out["summary"]["proof_markers_satisfied"] == 2
    assert {row["status"] for row in out["proof_markers"]} == {"satisfied_artifact"}
    assert all(row["artifact_status"]["artifact_id"] == "cost_assumptions" for row in out["proof_markers"])
    assert all(row["next_action"] == "none" for row in out["proof_markers"])


def test_report_operator_proof_status_cli(monkeypatch, capsys) -> None:
    from scripts import report_operator_proof_status as script

    monkeypatch.setattr(
        script,
        "build_operator_proof_status",
        lambda repo_root=None, category=None, line=None, passive_ordinal=None: {
            "ok": True,
            "reason": None,
            "category_filter": category,
            "available_categories": ["remaining_proof"],
            "line_filter": int(line) if line else None,
            "passive_operator_ordinal_filter": int(passive_ordinal) if passive_ordinal else None,
            "passive_operator_item_count": 1,
            "proof_marker_count": 1,
            "summary": {
                "remaining_proof_or_coverage_markers": 1,
                "host_side_markers": 0,
                "proof_ready_markers": 0,
            },
            "passive_operator_items": [{"ordinal": 1, "text": "Run host proof"}],
            "proof_markers": [
                {
                    "line": 7,
                    "category": "remaining_proof",
                    "text": "Remaining proof: run it",
                    "next_action": "produce or record the remaining proof referenced at REMAINING_TASKS.md:L7",
                }
            ],
        },
    )

    assert script.main(["--category", "remaining_proof", "--line", "7", "--passive-ordinal", "1"]) == 0
    out = capsys.readouterr().out
    assert "Operator Proof Status" in out
    assert "category_filter=remaining_proof" in out
    assert "line_filter=7" in out
    assert "passive_operator_ordinal_filter=1" in out
    assert "passive_items=1" in out
    assert "Run host proof" in out
    assert "L7 remaining_proof" in out
    assert "next_action=produce or record" in out


def test_report_operator_proof_status_cli_prints_invalid_category(capsys, monkeypatch) -> None:
    from scripts import report_operator_proof_status as script

    monkeypatch.setattr(
        script,
        "build_operator_proof_status",
        lambda repo_root=None, category=None, line=None, passive_ordinal=None: {
            "ok": False,
            "reason": "invalid_category",
            "category_filter": category,
            "available_categories": ["host_side_reference", "remaining_proof"],
            "line_filter": None,
            "passive_operator_ordinal_filter": None,
            "passive_operator_item_count": 0,
            "proof_marker_count": 0,
            "summary": {},
            "passive_operator_items": [],
            "proof_markers": [],
        },
    )

    assert script.main(["--category", "missing_category"]) == 2
    out = capsys.readouterr().out
    assert "reason=invalid_category" in out
    assert "available_categories=host_side_reference,remaining_proof" in out
