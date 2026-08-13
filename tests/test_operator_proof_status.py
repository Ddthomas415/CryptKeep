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


def test_operator_proof_status_treats_passive_lane_owned_remaining_proof_as_context_only(
    tmp_path: Path,
) -> None:
    from services.analytics.operator_proof_status import build_operator_proof_status

    _write_docs(tmp_path)
    (tmp_path / "REMAINING_TASKS.md").write_text(
        "\n".join(
            [
                "1. Backup.",
                "   Remaining proof: fresh backup/restore drill evidence and backup-artifact secrets scan.",
                "2. Cost.",
                "   Remaining proof: accepted shadow-derived cost-stack report with maker/taker bps.",
                "3. Local.",
                "   Remaining proof: execute the local invariant check.",
            ]
        ),
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path, category="remaining_proof")

    assert out["ok"] is True
    assert out["proof_marker_count"] == 3
    assert out["summary"]["proof_markers_context_only"] == 2
    assert out["summary"]["proof_marker_actions_required"] == 1
    rows = {row["line"]: row for row in out["proof_markers"]}
    assert rows[2]["status"] == "context_only"
    assert rows[2]["action_required"] is False
    assert rows[2]["next_action"] == "none"
    assert rows[4]["status"] == "context_only"
    assert rows[4]["action_required"] is False
    assert rows[6]["status"] == "open"
    assert rows[6]["action_required"] is True


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


def test_operator_proof_status_closes_accepted_proof_ready_cluster(tmp_path: Path) -> None:
    from services.analytics.operator_proof_status import build_operator_proof_status

    _write_docs(tmp_path)
    (tmp_path / "REMAINING_TASKS.md").write_text(
        "\n".join(
            [
                "1. Decimal migration.",
                "   2026-07-13 order-boundary slice is proof-ready for independent review.",
                "   2026-07-14 risk-gate slice is proof-ready for independent review.",
                "   2026-08-13: implementation slices accepted after independent review.",
                "2. Still open.",
                "   2026-07-15 another slice is proof-ready for independent review.",
            ]
        ),
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path, category="proof_ready_implementation")

    assert out["ok"] is True
    assert out["proof_marker_count"] == 3
    assert out["summary"]["proof_markers_satisfied"] == 2
    assert out["summary"]["proof_marker_actions_required"] == 1
    rows = {row["line"]: row for row in out["proof_markers"]}
    assert rows[2]["status"] == "satisfied_recorded"
    assert rows[2]["action_required"] is False
    assert rows[2]["next_action"] == "none"
    assert rows[3]["status"] == "satisfied_recorded"
    assert rows[3]["action_required"] is False
    assert rows[6]["status"] == "open"
    assert rows[6]["action_required"] is True


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


def test_operator_proof_status_marks_manual_strategy_decision_event_satisfied(tmp_path: Path) -> None:
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
                "- Manual strategy performance decision after the paper gate reaches the configured threshold.",
                "- Composite/hybrid paper advancement decision after evidence changes.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")
    journal = tmp_path / ".cbp_state" / "data" / "operator_events" / "operator_events.jsonl"
    journal.parent.mkdir(parents=True)
    journal.write_text(
        json.dumps(
            {
                "event_id": "evt-manual-decision",
                "timestamp": "2026-08-08T20:20:00Z",
                "actor": "operator",
                "action": "passive_operator_decision",
                "target": "manual_strategy_performance_decision",
                "result": "accepted",
                "reason": "paper_gate_review",
                "pre_state": {},
                "post_state": {},
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is True
    manual = out["passive_operator_items"][0]
    assert manual["action_required"] is False
    assert manual["next_action"] == "none"
    assert manual["artifact_status"]["artifact_id"] == "operator_decision_event"
    assert manual["artifact_status"]["artifact_status"] == "recorded"
    assert manual["artifact_status"]["event_id"] == "evt-manual-decision"
    assert manual["artifact_status"]["target"] == "manual_strategy_performance_decision"
    assert out["passive_operator_items"][1]["action_required"] is True


def test_operator_proof_status_shows_manual_strategy_decision_record_command(tmp_path: Path) -> None:
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
                "- Manual strategy performance decision after the paper gate reaches the configured threshold.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")
    artifact_dir = tmp_path / ".cbp_state" / "data" / "paper_gate_velocity"
    artifact_dir.mkdir(parents=True)
    (artifact_dir / "paper_gate_velocity.latest.json").write_text(
        json.dumps(
            {
                "ok": True,
                "read_only": True,
                "report_type": "paper_gate_velocity",
                "generated_at": "2026-08-08T00:00:00+00:00",
                "strategy_id": "es_daily_trend_v1",
                "thresholds_ready": True,
                "round_trips": {"qualified": 5, "required": 5, "remaining": 0},
                "qualified_bars": {"recorded": 60, "required": 60, "remaining": 0},
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is True
    manual = out["passive_operator_items"][0]
    assert manual["action_required"] is True
    assert manual["next_action"] == "make record-manual-strategy-performance-decision OPERATOR_DECISION_REASON='<reason>'"
    assert manual["artifact_status"]["artifact_status"] == "missing"
    assert manual["artifact_status"]["record_command"] == manual["next_action"]
    assert manual["artifact_status"]["paper_gate_velocity"]["thresholds_ready"] is True


def test_operator_proof_status_waits_for_paper_gate_before_manual_decision(tmp_path: Path) -> None:
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
                "- Manual strategy performance decision after the paper gate reaches the configured threshold.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")
    artifact_dir = tmp_path / ".cbp_state" / "data" / "paper_gate_velocity"
    artifact_dir.mkdir(parents=True)
    (artifact_dir / "paper_gate_velocity.latest.json").write_text(
        json.dumps(
            {
                "ok": True,
                "read_only": True,
                "report_type": "paper_gate_velocity",
                "generated_at": "2026-08-08T00:00:00+00:00",
                "strategy_id": "es_daily_trend_v1",
                "thresholds_ready": False,
                "round_trips": {"qualified": 3, "required": 5, "remaining": 2},
                "qualified_bars": {"recorded": 47, "required": 60, "remaining": 13},
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is True
    manual = out["passive_operator_items"][0]
    assert manual["action_required"] is False
    assert manual["next_action"] == "none"
    assert manual["artifact_status"]["artifact_status"] == "waiting_for_paper_gate_threshold"
    assert manual["artifact_status"]["paper_gate_velocity"]["round_trips"]["remaining"] == 2
    assert out["summary"]["passive_operator_items_satisfied"] == 0
    assert out["summary"]["passive_operator_items_waiting"] == 1


def test_operator_proof_status_does_not_surface_future_promotion_host_marker_before_gate(
    tmp_path: Path,
) -> None:
    from services.analytics.operator_proof_status import build_operator_proof_status

    _write_docs(tmp_path)
    (tmp_path / "REMAINING_TASKS.md").write_text(
        "\n".join(
            [
                "2. After the paper gate reaches 10 qualified round trips, write the manual strategy performance decision.",
                "   Ground truth must come from the operator-host gate/status command output.",
                "   Remaining before real promotion: GitHub CI/review, plus operator-host gate output as ground truth.",
            ]
        ),
        encoding="utf-8",
    )
    artifact_dir = tmp_path / ".cbp_state" / "data" / "paper_gate_velocity"
    artifact_dir.mkdir(parents=True)
    (artifact_dir / "paper_gate_velocity.latest.json").write_text(
        json.dumps(
            {
                "ok": True,
                "read_only": True,
                "report_type": "paper_gate_velocity",
                "generated_at": "2026-08-13T00:00:00+00:00",
                "strategy_id": "es_daily_trend_v1",
                "thresholds_ready": False,
                "round_trips": {"qualified": 3, "required": 5, "remaining": 2},
                "qualified_bars": {"recorded": 52, "required": 60, "remaining": 8},
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path, category="host_side_reference")

    assert out["ok"] is True
    assert out["proof_marker_count"] == 2
    assert out["summary"]["proof_marker_actions_required"] == 0
    for row in out["proof_markers"]:
        assert row["action_required"] is False
        assert row["next_action"] == "none"
        assert row["artifact_status"]["artifact_status"] == "waiting_for_paper_gate_threshold"


def test_operator_proof_status_marks_composite_decision_event_satisfied(tmp_path: Path) -> None:
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
                "- Composite/hybrid paper advancement decision after evidence changes.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")
    journal = tmp_path / ".cbp_state" / "data" / "operator_events" / "operator_events.jsonl"
    journal.parent.mkdir(parents=True)
    journal.write_text(
        json.dumps(
            {
                "event_id": "evt-composite-decision",
                "timestamp": "2026-08-08T20:20:01Z",
                "actor": "operator",
                "action": "passive_operator_decision",
                "target": "composite_hybrid_paper_advancement_decision",
                "result": "declined",
                "reason": "insufficient_edge",
                "pre_state": {},
                "post_state": {},
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is True
    composite = out["passive_operator_items"][0]
    assert composite["action_required"] is False
    assert composite["next_action"] == "none"
    assert composite["artifact_status"]["artifact_status"] == "recorded"
    assert composite["artifact_status"]["result"] == "declined"


def test_operator_proof_status_tracks_restricted_sandbox_exception(tmp_path: Path) -> None:
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
                "- Private sandbox/testnet lifecycle proof or explicit accepted exception.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")
    evidence_dir = tmp_path / ".cbp_state" / "data" / "exchange_sandbox_smoke"
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "exchange-sandbox-smoke-20260811T000000Z.json").write_text(
        json.dumps(
            {
                "report_type": "exchange_sandbox_smoke",
                "ok": False,
                "read_only": True,
                "sandbox": True,
                "exchange": "binance",
                "symbol": "BTC/USDT",
                "checks": [
                    {
                        "name": "orderbook",
                        "ok": False,
                        "error": "Service unavailable from a restricted location according to 'b. Eligibility'",
                    }
                ],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    blocked = build_operator_proof_status(repo_root=tmp_path)
    item = blocked["passive_operator_items"][0]
    assert item["action_required"] is True
    assert item["artifact_status"]["artifact_status"] == "blocked_restricted_location"
    assert item["artifact_status"]["restricted_location"] is True
    assert "record-exchange-sandbox-exception" in item["next_action"]

    journal = tmp_path / ".cbp_state" / "data" / "operator_events" / "operator_events.jsonl"
    journal.parent.mkdir(parents=True, exist_ok=True)
    journal.write_text(
        json.dumps(
            {
                "event_id": "evt-sandbox-exception",
                "timestamp": "2026-08-11T20:30:00Z",
                "actor": "operator",
                "action": "passive_operator_decision",
                "target": "exchange_sandbox_restricted_location_exception",
                "result": "accepted_with_risk",
                "reason": "binance sandbox is blocked from this location",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    accepted = build_operator_proof_status(repo_root=tmp_path)
    item = accepted["passive_operator_items"][0]
    assert item["action_required"] is False
    assert item["next_action"] == "none"
    assert item["artifact_status"]["artifact_status"] == "accepted_restricted_location_exception"
    assert item["artifact_status"]["exception_event"]["event_id"] == "evt-sandbox-exception"


def test_operator_proof_status_marks_archive_research_passive_item_satisfied(tmp_path: Path) -> None:
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
                "- Real multi-year archive sweeps and separate review before any strategy config or campaign uses sweep results.",
                "- Another proof.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")
    artifact_root = tmp_path / ".cbp_state" / "data" / "research"
    (artifact_root / "archive_walk_forward").mkdir(parents=True)
    (artifact_root / "archive_parameter_sweep").mkdir()
    (artifact_root / "archive_parameter_sweep_triage").mkdir()
    (artifact_root / "archive_walk_forward" / "wf.latest.json").write_text(
        json.dumps({"artifact_type": "archive_backed_walk_forward_v1", "ok": True}),
        encoding="utf-8",
    )
    (artifact_root / "archive_parameter_sweep" / "sweep.latest.json").write_text(
        json.dumps({"artifact_type": "archive_backed_parameter_sweep_v1", "ok": True}),
        encoding="utf-8",
    )
    (artifact_root / "archive_parameter_sweep_triage" / "triage.latest.json").write_text(
        json.dumps(
            {
                "artifact_type": "archive_parameter_sweep_triage_v1",
                "ok": False,
                "reason": "insufficient_review_candidates",
                "candidates": [],
                "review_candidates": [],
            }
        ),
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is True
    archive = out["passive_operator_items"][0]
    assert archive["action_required"] is False
    assert archive["next_action"] == "none"
    assert archive["artifact_status"]["artifact_id"] == "archive_research_evidence"
    assert archive["artifact_status"]["artifact_status"] == "recorded"
    assert archive["artifact_status"]["satisfied"] is True
    assert len(archive["artifact_status"]["artifacts"]) == 3
    assert out["passive_operator_items"][1]["action_required"] is True


def test_operator_proof_status_attaches_funding_research_without_satisfying_decision(
    tmp_path: Path,
) -> None:
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
                "- `funding_extreme` persistent-campaign decision after reviewed price-joined research shows an actionable basis.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")
    run_dir = tmp_path / ".cbp_state" / "data" / "research" / "funding_threshold_pipeline" / "run"
    run_dir.mkdir(parents=True)
    (run_dir / "pipeline_summary.json").write_text(
        json.dumps({"report_type": "funding_threshold_research_pipeline", "ok": True, "read_only": True}),
        encoding="utf-8",
    )
    (run_dir / "funding_context_price_join.json").write_text(
        json.dumps({"artifact_type": "funding_context_price_join_v1", "ok": True}),
        encoding="utf-8",
    )
    (run_dir / "funding_threshold_candidate_triage.json").write_text(
        json.dumps(
            {
                "artifact_type": "funding_threshold_candidate_triage_v1",
                "ok": True,
                "candidates": [{"status": "not_candidate"}],
                "review_candidates": [],
            }
        ),
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is True
    funding = out["passive_operator_items"][0]
    assert funding["action_required"] is False
    assert funding["next_action"] == "none"
    assert funding["artifact_status"]["artifact_id"] == "funding_research_evidence"
    assert funding["artifact_status"]["artifact_status"] == "no_actionable_basis"
    assert funding["artifact_status"]["satisfied"] is False
    assert funding["artifact_status"]["evidence_recorded"] is True
    assert funding["artifact_status"]["actionable_basis"] is False
    assert funding["artifact_status"]["candidate_count"] == 0
    assert funding["artifact_status"]["decision_event"]["satisfied"] is False
    assert out["summary"]["passive_operator_items_satisfied"] == 0
    assert out["summary"]["passive_operator_items_waiting"] == 1


def test_operator_proof_status_prompts_funding_decision_with_actionable_basis(
    tmp_path: Path,
) -> None:
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
                "- `funding_extreme` persistent-campaign decision after reviewed price-joined research shows an actionable basis.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")
    run_dir = tmp_path / ".cbp_state" / "data" / "research" / "funding_threshold_pipeline" / "run"
    run_dir.mkdir(parents=True)
    (run_dir / "pipeline_summary.json").write_text(
        json.dumps({"report_type": "funding_threshold_research_pipeline", "ok": True, "read_only": True}),
        encoding="utf-8",
    )
    (run_dir / "funding_context_price_join.json").write_text(
        json.dumps({"artifact_type": "funding_context_price_join_v1", "ok": True}),
        encoding="utf-8",
    )
    (run_dir / "funding_threshold_candidate_triage.json").write_text(
        json.dumps(
            {
                "artifact_type": "funding_threshold_candidate_triage_v1",
                "ok": True,
                "candidates": [{"status": "candidate", "candidate_id": "funding-a"}],
                "review_candidates": [{"status": "candidate", "candidate_id": "funding-a"}],
            }
        ),
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is True
    funding = out["passive_operator_items"][0]
    assert funding["action_required"] is True
    assert funding["next_action"] == (
        "make record-funding-extreme-persistent-campaign-decision "
        "FUNDING_EXTREME_PERSISTENT_CAMPAIGN_DECISION_RESULT=accepted "
        "OPERATOR_DECISION_REASON='<reason>'"
    )
    assert funding["artifact_status"]["artifact_status"] == "actionable_basis_recorded"
    assert funding["artifact_status"]["actionable_basis"] is True
    assert funding["artifact_status"]["candidate_count"] == 1


def test_operator_proof_status_marks_funding_decision_event_satisfied(
    tmp_path: Path,
) -> None:
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
                "- `funding_extreme` persistent-campaign decision after reviewed price-joined research shows an actionable basis.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")
    run_dir = tmp_path / ".cbp_state" / "data" / "research" / "funding_threshold_pipeline" / "run"
    run_dir.mkdir(parents=True)
    (run_dir / "pipeline_summary.json").write_text(
        json.dumps({"report_type": "funding_threshold_research_pipeline", "ok": True, "read_only": True}),
        encoding="utf-8",
    )
    (run_dir / "funding_context_price_join.json").write_text(
        json.dumps({"artifact_type": "funding_context_price_join_v1", "ok": True}),
        encoding="utf-8",
    )
    (run_dir / "funding_threshold_candidate_triage.json").write_text(
        json.dumps(
            {
                "artifact_type": "funding_threshold_candidate_triage_v1",
                "ok": True,
                "candidates": [{"status": "not_candidate"}],
                "review_candidates": [],
            }
        ),
        encoding="utf-8",
    )
    journal = tmp_path / ".cbp_state" / "data" / "operator_events" / "operator_events.jsonl"
    journal.parent.mkdir(parents=True, exist_ok=True)
    journal.write_text(
        json.dumps(
            {
                "event_id": "evt-funding-no-campaign",
                "timestamp": "2026-08-08T20:20:02Z",
                "actor": "operator",
                "action": "passive_operator_decision",
                "target": "funding_extreme_persistent_campaign_decision",
                "result": "no_persistent_campaign",
                "reason": "candidate_count_zero",
                "pre_state": {},
                "post_state": {},
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is True
    funding = out["passive_operator_items"][0]
    assert funding["action_required"] is False
    assert funding["next_action"] == "none"
    assert funding["artifact_status"]["artifact_status"] == "decision_recorded"
    assert funding["artifact_status"]["decision_event"]["event_id"] == "evt-funding-no-campaign"
    assert funding["artifact_status"]["decision_event"]["result"] == "no_persistent_campaign"


def test_operator_proof_status_shows_command_guidance_without_satisfying_rows(tmp_path: Path) -> None:
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
                "- Private sandbox/testnet lifecycle proof or explicit accepted exception.",
                "- Launch evidence packet: restart, recovery, kill-switch, reconcile, rollback.",
                "- Accepted shadow-derived execution-cost report using those records.",
                "- Backup/restore drill evidence and backup-artifact secrets scan.",
                "- Supply-chain audit/waiver evidence.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is True
    rows = out["passive_operator_items"]
    assert rows[0]["artifact_status"]["artifact_id"] == "exchange_sandbox_smoke_guidance"
    assert rows[0]["action_required"] is True
    assert rows[0]["next_action"] == "make record-exchange-sandbox-smoke"
    assert rows[1]["artifact_status"]["artifact_id"] == "launch_packet_replay_guidance"
    assert rows[1]["action_required"] is True
    assert rows[1]["next_action"] == "make record-operator-arm-to-halt-replay"
    assert rows[2]["artifact_status"]["artifact_id"] == "execution_cost_stack_report"
    assert rows[2]["artifact_status"]["artifact_status"] == "waiting_for_shadow_would_be_fill_records"
    assert rows[2]["action_required"] is False
    assert rows[2]["next_action"] == "none"
    assert rows[3]["artifact_status"]["artifact_id"] == "state_backup_restore_drill"
    assert rows[3]["artifact_status"]["artifact_status"] == "missing_or_incomplete"
    assert rows[3]["action_required"] is True
    assert rows[3]["next_action"] == "make backup-state STATE_BACKUP_DEST=<backup_dir>"
    assert rows[4]["artifact_status"]["artifact_id"] == "supply_chain_audit_guidance"
    assert rows[4]["action_required"] is True
    assert rows[4]["next_action"] == "make record-supply-chain"
    assert out["summary"]["passive_operator_items_satisfied"] == 0
    assert out["summary"]["passive_operator_items_waiting"] == 1
    assert out["summary"]["passive_operator_items_action_required"] == 4


def test_operator_proof_status_marks_exchange_sandbox_smoke_satisfied(tmp_path: Path) -> None:
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
                "- Private sandbox/testnet lifecycle proof or explicit accepted exception.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")
    evidence_dir = tmp_path / ".cbp_state" / "data" / "exchange_sandbox_smoke"
    evidence_dir.mkdir(parents=True)
    artifact = evidence_dir / "exchange-sandbox-smoke-20260809T000000Z.json"
    artifact.write_text(
        json.dumps(
            {
                "report_type": "exchange_sandbox_smoke",
                "created": "2026-08-09T00:00:00Z",
                "read_only": True,
                "ok": True,
                "exchange": "binance",
                "symbol": "BTC/USD",
                "sandbox": True,
                "checks": [
                    {"name": "build_exchange", "ok": True},
                    {"name": "fetch_ticker", "ok": True},
                    {"name": "fetch_order_book", "ok": True},
                ],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is True
    sandbox = out["passive_operator_items"][0]
    assert sandbox["action_required"] is False
    assert sandbox["next_action"] == "none"
    assert sandbox["artifact_status"]["artifact_id"] == "exchange_sandbox_smoke"
    assert sandbox["artifact_status"]["artifact_status"] == "recorded"
    assert sandbox["artifact_status"]["exchange"] == "binance"
    assert sandbox["artifact_status"]["check_count"] == 3
    assert out["summary"]["passive_operator_items_satisfied"] == 1


def test_operator_proof_status_keeps_failed_exchange_sandbox_smoke_open(tmp_path: Path) -> None:
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
                "- Private sandbox/testnet lifecycle proof or explicit accepted exception.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")
    evidence_dir = tmp_path / ".cbp_state" / "data" / "exchange_sandbox_smoke"
    evidence_dir.mkdir(parents=True)
    artifact = evidence_dir / "exchange-sandbox-smoke-20260809T000000Z.json"
    artifact.write_text(
        json.dumps(
            {
                "report_type": "exchange_sandbox_smoke",
                "created": "2026-08-09T00:00:00Z",
                "read_only": True,
                "ok": False,
                "exchange": "binance",
                "symbol": "BTC/USD",
                "sandbox": True,
                "checks": [{"name": "fetch_ticker", "ok": False}],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is True
    sandbox = out["passive_operator_items"][0]
    assert sandbox["action_required"] is True
    assert sandbox["next_action"] == "make record-exchange-sandbox-smoke"
    assert sandbox["artifact_status"]["artifact_status"] == "invalid_or_failed"
    assert out["summary"]["passive_operator_items_satisfied"] == 0


def test_operator_proof_status_surfaces_restricted_exchange_sandbox_smoke(tmp_path: Path) -> None:
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
                "- Private sandbox/testnet lifecycle proof or explicit accepted exception.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")
    evidence_dir = tmp_path / ".cbp_state" / "data" / "exchange_sandbox_smoke"
    evidence_dir.mkdir(parents=True)
    artifact = evidence_dir / "exchange-sandbox-smoke-20260809T000000Z.json"
    artifact.write_text(
        json.dumps(
            {
                "report_type": "exchange_sandbox_smoke",
                "created": "2026-08-09T00:00:00Z",
                "read_only": True,
                "ok": False,
                "exchange": "binance",
                "symbol": "BTC/USD",
                "sandbox": True,
                "checks": [
                    {
                        "name": "fetch_ticker",
                        "ok": False,
                        "error": "ExchangeNotAvailable: Service unavailable from a restricted location",
                    }
                ],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path)

    sandbox = out["passive_operator_items"][0]
    assert sandbox["action_required"] is True
    assert "record-exchange-sandbox-exception" in sandbox["next_action"]
    assert "configure a reachable sandbox exchange" in sandbox["next_action"]
    assert sandbox["artifact_status"]["artifact_status"] == "blocked_restricted_location"
    assert sandbox["artifact_status"]["restricted_location"] is True


def test_operator_proof_status_marks_arm_to_halt_replay_evidence_satisfied(tmp_path: Path) -> None:
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
                "- Launch evidence packet: restart, recovery, kill-switch, reconcile, rollback.",
                "- Backup/restore drill evidence and backup-artifact secrets scan.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")
    evidence = tmp_path / ".cbp_state" / "data" / "operator_arm_to_halt_replay"
    evidence.mkdir(parents=True)
    (evidence / "operator-arm-to-halt-replay-20260809T000000Z.json").write_text(
        json.dumps(
            {
                "created": "2026-08-09T00:00:00Z",
                "ok": True,
                "reason": "ok",
                "event_count": 2,
                "arm_event": {"event_id": "evt-arm", "action": "live_enable"},
                "halt_event": {"event_id": "evt-halt", "action": "live_halt"},
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is True
    replay = out["passive_operator_items"][0]
    assert replay["action_required"] is False
    assert replay["next_action"] == "none"
    assert replay["artifact_status"]["artifact_id"] == "operator_arm_to_halt_replay"
    assert replay["artifact_status"]["artifact_status"] == "recorded"
    assert replay["artifact_status"]["arm_event"]["event_id"] == "evt-arm"
    assert replay["artifact_status"]["halt_event"]["event_id"] == "evt-halt"
    assert out["passive_operator_items"][1]["action_required"] is True
    assert out["summary"]["passive_operator_items_satisfied"] == 1


def test_operator_proof_status_keeps_failed_arm_to_halt_replay_open(tmp_path: Path) -> None:
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
                "- Launch evidence packet: restart, recovery, kill-switch, reconcile, rollback.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")
    evidence = tmp_path / ".cbp_state" / "data" / "operator_arm_to_halt_replay"
    evidence.mkdir(parents=True)
    (evidence / "operator-arm-to-halt-replay-20260809T000000Z.json").write_text(
        json.dumps(
            {
                "created": "2026-08-09T00:00:00Z",
                "ok": False,
                "reason": "missing_live_halt_event_after_arm",
                "event_count": 1,
                "arm_event": {"event_id": "evt-arm"},
                "halt_event": None,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is True
    replay = out["passive_operator_items"][0]
    assert replay["action_required"] is True
    assert replay["next_action"] == "make record-operator-arm-to-halt-replay"
    assert replay["artifact_status"]["artifact_status"] == "missing_live_halt_event_after_arm"
    assert out["summary"]["passive_operator_items_satisfied"] == 0


def test_operator_proof_status_marks_backup_restore_drill_satisfied(tmp_path: Path) -> None:
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
                "- Backup/restore drill evidence and backup-artifact secrets scan.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")
    journal = tmp_path / ".cbp_state" / "data" / "operator_events" / "operator_events.jsonl"
    journal.parent.mkdir(parents=True)
    events = [
        {
            "event_id": "evt-backup",
            "timestamp": "2026-08-09T00:00:00Z",
            "actor": "operator",
            "action": "state_backup",
            "target": "state_dir",
            "result": "success",
            "reason": "backup",
            "post_state": {"ok": True, "backup_dir": "/tmp/backup", "file_count": 2},
        },
        {
            "event_id": "evt-verify",
            "timestamp": "2026-08-09T00:01:00Z",
            "actor": "operator",
            "action": "state_backup_verify",
            "target": "state_dir",
            "result": "success",
            "reason": "verify",
            "pre_state": {"args": {"backup_dir": "/tmp/backup"}},
            "post_state": {"ok": True},
        },
        {
            "event_id": "evt-restore",
            "timestamp": "2026-08-09T00:02:00Z",
            "actor": "operator",
            "action": "state_restore",
            "target": "state_dir",
            "result": "success",
            "reason": "restore",
            "pre_state": {"args": {"backup_dir": "/tmp/backup"}},
            "post_state": {"ok": True},
        },
        {
            "event_id": "evt-secret-scan",
            "timestamp": "2026-08-09T00:02:30Z",
            "actor": "operator",
            "action": "state_backup_secret_scan",
            "target": "state_dir",
            "result": "success",
            "reason": "backup_artifact_secret_scan",
            "pre_state": {"backup_dir": "/tmp/backup"},
            "post_state": {"ok": True, "finding_count": 0},
        },
        {
            "event_id": "evt-checkpoint",
            "timestamp": "2026-08-09T00:03:00Z",
            "actor": "operator",
            "action": "runbook_checkpoint",
            "target": "state_backup_restore_drill",
            "result": "completed",
            "reason": "restore_and_secret_scan_reviewed",
        },
    ]
    journal.write_text("\n".join(json.dumps(event, sort_keys=True) for event in events) + "\n", encoding="utf-8")

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is True
    drill = out["passive_operator_items"][0]
    assert drill["action_required"] is False
    assert drill["next_action"] == "none"
    assert drill["artifact_status"]["artifact_id"] == "state_backup_restore_drill"
    assert drill["artifact_status"]["artifact_status"] == "recorded"
    assert drill["artifact_status"]["events"]["backup"]["event_id"] == "evt-backup"
    assert drill["artifact_status"]["events"]["verify"]["event_id"] == "evt-verify"
    assert drill["artifact_status"]["events"]["restore"]["event_id"] == "evt-restore"
    assert drill["artifact_status"]["events"]["secret_scan"]["event_id"] == "evt-secret-scan"
    assert drill["artifact_status"]["events"]["checkpoint"]["event_id"] == "evt-checkpoint"
    assert out["summary"]["passive_operator_items_satisfied"] == 1


def test_operator_proof_status_keeps_backup_restore_open_without_secret_scan(tmp_path: Path) -> None:
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
                "- Backup/restore drill evidence and backup-artifact secrets scan.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")
    journal = tmp_path / ".cbp_state" / "data" / "operator_events" / "operator_events.jsonl"
    journal.parent.mkdir(parents=True)
    events = [
        {"event_id": "evt-backup", "action": "state_backup", "target": "state_dir", "result": "success"},
        {"event_id": "evt-verify", "action": "state_backup_verify", "target": "state_dir", "result": "success"},
        {"event_id": "evt-restore", "action": "state_restore", "target": "state_dir", "result": "success"},
    ]
    journal.write_text("\n".join(json.dumps(event, sort_keys=True) for event in events) + "\n", encoding="utf-8")

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is True
    drill = out["passive_operator_items"][0]
    assert drill["action_required"] is True
    assert drill["next_action"] == "make check-backup-artifact-secrets STATE_BACKUP_ARTIFACT=<backup_dir>"
    assert drill["artifact_status"]["artifact_status"] == "missing_or_incomplete"
    assert drill["artifact_status"]["events"]["restore"]["event_id"] == "evt-restore"
    assert drill["artifact_status"]["events"]["secret_scan"] is None
    assert drill["artifact_status"]["events"]["checkpoint"] is None
    assert out["summary"]["passive_operator_items_satisfied"] == 0


def test_operator_proof_status_keeps_backup_restore_open_without_checkpoint_after_secret_scan(tmp_path: Path) -> None:
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
                "- Backup/restore drill evidence and backup-artifact secrets scan.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")
    journal = tmp_path / ".cbp_state" / "data" / "operator_events" / "operator_events.jsonl"
    journal.parent.mkdir(parents=True)
    events = [
        {"event_id": "evt-backup", "action": "state_backup", "target": "state_dir", "result": "success"},
        {"event_id": "evt-verify", "action": "state_backup_verify", "target": "state_dir", "result": "success"},
        {"event_id": "evt-restore", "action": "state_restore", "target": "state_dir", "result": "success"},
        {"event_id": "evt-secret-scan", "action": "state_backup_secret_scan", "target": "state_dir", "result": "success"},
    ]
    journal.write_text("\n".join(json.dumps(event, sort_keys=True) for event in events) + "\n", encoding="utf-8")

    out = build_operator_proof_status(repo_root=tmp_path)

    drill = out["passive_operator_items"][0]
    assert drill["action_required"] is True
    assert drill["next_action"] == "make record-backup-restore-drill-checkpoint OPERATOR_CHECKPOINT_REASON='<reason>'"
    assert drill["artifact_status"]["events"]["secret_scan"]["event_id"] == "evt-secret-scan"
    assert drill["artifact_status"]["events"]["checkpoint"] is None


def test_operator_proof_status_marks_supply_chain_evidence_satisfied(tmp_path: Path) -> None:
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
                "- Supply-chain audit/waiver evidence.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")
    evidence_dir = tmp_path / ".cbp_state" / "data" / "supply_chain"
    evidence_dir.mkdir(parents=True)
    artifact = evidence_dir / "supply-chain-evidence-20260808T203600Z.json"
    artifact.write_text(
        json.dumps(
            {
                "created": "2026-08-08T20:36:00Z",
                "git_sha": "abc123",
                "git_dirty": False,
                "requirement_file_sha256": {"requirements-pinned.txt": "sha"},
                "pin_integrity": {"ok": True, "problems": [], "pin_count": 1},
                "environment": {"ok": True, "checked": 1, "mismatches": [], "not_installed": []},
                "vulnerability_audit": {"ran": False, "reason": "not_requested"},
            }
        ),
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is True
    supply = out["passive_operator_items"][0]
    assert supply["action_required"] is False
    assert supply["next_action"] == "none"
    assert supply["artifact_status"]["artifact_id"] == "supply_chain_evidence"
    assert supply["artifact_status"]["artifact_status"] == "recorded"
    assert supply["artifact_status"]["pin_integrity_ok"] is True
    assert supply["artifact_status"]["environment_ok"] is True
    assert out["summary"]["passive_operator_items_satisfied"] == 1


def test_operator_proof_status_marks_execution_cost_report_satisfied(tmp_path: Path) -> None:
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
                "- Accepted shadow-derived execution-cost report using those records.",
                "- Supply-chain audit/waiver evidence.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")
    latest = tmp_path / ".cbp_state" / "data" / "execution_cost_stack" / "execution_cost_stack.latest.json"
    latest.parent.mkdir(parents=True)
    latest.write_text(
        json.dumps(
            {
                "report_type": "execution_cost_stack_report",
                "generated_at": "2026-08-09T01:00:00+00:00",
                "read_only": True,
                "scope": "research_only_shadow_would_be_fill_records",
                "source_report_hash": "abc123",
                "source_artifact_hash": "def456",
                "recommendation": "research_more",
                "parse_errors": 0,
                "policy": {
                    "no_live_routing_changes": True,
                    "no_order_type_policy_changes": True,
                    "no_canonical_paper_campaign_changes": True,
                    "paper_fills_excluded": True,
                },
                "summary": {"record_count": 3},
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is True
    cost = out["passive_operator_items"][0]
    assert cost["action_required"] is False
    assert cost["next_action"] == "none"
    assert cost["artifact_status"]["artifact_id"] == "execution_cost_stack_report"
    assert cost["artifact_status"]["artifact_status"] == "recorded"
    assert cost["artifact_status"]["recommendation"] == "research_more"
    assert cost["artifact_status"]["source_report_hash"] == "abc123"
    assert out["passive_operator_items"][1]["action_required"] is True
    assert out["summary"]["passive_operator_items_satisfied"] == 1


def test_operator_proof_status_prompts_execution_cost_report_after_shadow_records(tmp_path: Path) -> None:
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
                "- Accepted shadow-derived execution-cost report using those records.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")
    evidence_file = tmp_path / ".cbp_state" / "data" / "evidence" / "shadow_session" / "fill_0001.jsonl"
    evidence_file.parent.mkdir(parents=True)
    evidence_file.write_text(
        json.dumps(
            {
                "record_subtype": "shadow_would_be_fill",
                "shadow_would_be_fill": True,
                "timestamp": "2026-08-08T20:00:00Z",
                "strategy_id": "es_daily_trend_v1",
                "intent_id": "intent-1",
                "reference_bid": 100.0,
                "reference_ask": 100.2,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is True
    cost = out["passive_operator_items"][0]
    assert cost["action_required"] is True
    assert cost["next_action"] == "make record-execution-cost-stack"
    assert cost["artifact_status"]["artifact_id"] == "execution_cost_stack_report_guidance"
    assert cost["artifact_status"]["artifact_status"] == "command_guidance"
    assert out["summary"]["passive_operator_items_satisfied"] == 0


def test_operator_proof_status_waits_for_shadow_records_before_execution_cost_report(tmp_path: Path) -> None:
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
                "- Accepted shadow-derived execution-cost report using those records.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is True
    cost = out["passive_operator_items"][0]
    assert cost["action_required"] is False
    assert cost["next_action"] == "none"
    assert cost["artifact_status"]["artifact_status"] == "waiting_for_shadow_would_be_fill_records"
    assert cost["artifact_status"]["shadow_would_be_fill"]["artifact_status"] == "missing"
    assert out["summary"]["passive_operator_items_satisfied"] == 0
    assert out["summary"]["passive_operator_items_waiting"] == 1


def test_operator_proof_status_keeps_invalid_execution_cost_report_open(tmp_path: Path) -> None:
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
                "- Accepted shadow-derived execution-cost report using those records.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")
    latest = tmp_path / ".cbp_state" / "data" / "execution_cost_stack" / "execution_cost_stack.latest.json"
    latest.parent.mkdir(parents=True)
    latest.write_text(
        json.dumps(
            {
                "report_type": "execution_cost_stack_report",
                "read_only": True,
                "scope": "research_only_shadow_would_be_fill_records",
                "recommendation": "research_more",
                "policy": {"paper_fills_excluded": True},
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is True
    cost = out["passive_operator_items"][0]
    assert cost["action_required"] is True
    assert cost["next_action"] == "make record-execution-cost-stack"
    assert cost["artifact_status"]["artifact_status"] == "invalid_or_incomplete"
    assert out["summary"]["passive_operator_items_satisfied"] == 0


def test_operator_proof_status_shows_runbook_guidance_without_satisfying_rows(tmp_path: Path) -> None:
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
                "- Accepted shadow-stage run producing real `shadow_would_be_fill` records.",
                "- Hetzner canonical `.cbp_state` migration follow-through.",
                "- Paper-to-shadow first-hour rehearsal.",
                "- Server secrets injection/rotation drill.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is True
    rows = out["passive_operator_items"]
    assert all(row["action_required"] is True for row in rows)
    assert rows[0]["artifact_status"]["artifact_id"] == "shadow_would_be_fill_records"
    assert rows[0]["artifact_status"]["artifact_status"] == "missing"
    assert rows[0]["artifact_status"]["record_count"] == 0
    assert rows[0]["artifact_status"]["doc_path"] == "docs/PAPER_TO_SHADOW_FIRST_HOUR_RUNBOOK.md"
    assert "shadow_would_be_fill" in rows[0]["next_action"]
    assert rows[1]["artifact_status"]["artifact_id"] == "hetzner_canonical_state_migration_guidance"
    assert rows[1]["artifact_status"]["doc_path"] == "docs/deployment_records/hetzner_canonical_state_migration_TEMPLATE.md"
    assert rows[1]["next_action"] == "make record-hetzner-state-migration-checkpoint OPERATOR_CHECKPOINT_REASON='<reason>'"
    assert rows[2]["artifact_status"]["artifact_id"] == "paper_to_shadow_first_hour_guidance"
    assert rows[2]["artifact_status"]["doc_path"] == "docs/PAPER_TO_SHADOW_FIRST_HOUR_RUNBOOK.md"
    assert rows[2]["next_action"] == "make record-paper-to-shadow-first-hour-checkpoint OPERATOR_CHECKPOINT_REASON='<reason>'"
    assert rows[3]["artifact_status"]["artifact_id"] == "server_secrets_rotation_guidance"
    assert rows[3]["artifact_status"]["doc_path"] == "docs/SERVER_SECRETS_ROTATION_MODEL.md"
    assert rows[3]["next_action"] == "make record-server-secrets-rotation-checkpoint OPERATOR_CHECKPOINT_REASON='<reason>'"
    assert out["summary"]["passive_operator_items_satisfied"] == 0


def test_operator_proof_status_marks_runbook_checkpoint_satisfied(tmp_path: Path) -> None:
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
                "- Paper-to-shadow first-hour rehearsal.",
                "- Server secrets injection/rotation drill.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")
    journal = tmp_path / ".cbp_state" / "data" / "operator_events" / "operator_events.jsonl"
    journal.parent.mkdir(parents=True)
    journal.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "event_id": "evt-shadow-rehearsal",
                        "timestamp": "2026-08-09T00:00:00Z",
                        "actor": "operator",
                        "action": "runbook_checkpoint",
                        "target": "paper_to_shadow_first_hour_rehearsal",
                        "result": "completed",
                        "reason": "rehearsed_without_runtime_changes",
                        "pre_state": {},
                        "post_state": {},
                    },
                    sort_keys=True,
                ),
                json.dumps(
                    {
                        "event_id": "evt-secrets-drill",
                        "timestamp": "2026-08-09T00:01:00Z",
                        "actor": "operator",
                        "action": "runbook_checkpoint",
                        "target": "server_secrets_rotation_drill",
                        "result": "accepted_with_risk",
                        "reason": "redacted_packet_reviewed",
                        "pre_state": {},
                        "post_state": {},
                    },
                    sort_keys=True,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is True
    rows = out["passive_operator_items"]
    assert all(row["action_required"] is False for row in rows)
    assert rows[0]["next_action"] == "none"
    assert rows[0]["artifact_status"]["artifact_status"] == "recorded"
    assert rows[0]["artifact_status"]["event_id"] == "evt-shadow-rehearsal"
    assert rows[1]["next_action"] == "none"
    assert rows[1]["artifact_status"]["artifact_status"] == "recorded"
    assert rows[1]["artifact_status"]["event_id"] == "evt-secrets-drill"
    assert out["summary"]["passive_operator_items_satisfied"] == 2


def test_operator_proof_status_marks_shadow_would_be_fill_records_satisfied(tmp_path: Path) -> None:
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
                "- Accepted shadow-stage run producing real `shadow_would_be_fill` records.",
                "- Paper-to-shadow first-hour rehearsal.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")
    evidence_file = tmp_path / ".cbp_state" / "data" / "evidence" / "shadow_session" / "fill_0001.jsonl"
    evidence_file.parent.mkdir(parents=True)
    evidence_file.write_text(
        json.dumps(
            {
                "record_subtype": "shadow_would_be_fill",
                "shadow_would_be_fill": True,
                "timestamp": "2026-08-08T20:00:00Z",
                "strategy_id": "es_daily_trend_v1",
                "intent_id": "intent-1",
                "reference_bid": 100.0,
                "reference_ask": 100.2,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is True
    shadow = out["passive_operator_items"][0]
    assert shadow["action_required"] is False
    assert shadow["next_action"] == "none"
    assert shadow["artifact_status"]["artifact_id"] == "shadow_would_be_fill_records"
    assert shadow["artifact_status"]["artifact_status"] == "recorded"
    assert shadow["artifact_status"]["record_count"] == 1
    assert shadow["artifact_status"]["parse_errors"] == 0
    assert shadow["artifact_status"]["source_artifact_hash"]
    assert out["passive_operator_items"][1]["action_required"] is True
    assert out["summary"]["passive_operator_items_satisfied"] == 1


def test_operator_proof_status_keeps_shadow_records_open_on_parse_errors(tmp_path: Path) -> None:
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
                "- Accepted shadow-stage run producing real `shadow_would_be_fill` records.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "REMAINING_TASKS.md").write_text("Remaining proof: run drill.", encoding="utf-8")
    evidence_file = tmp_path / ".cbp_state" / "data" / "evidence" / "shadow_session" / "fill_0001.jsonl"
    evidence_file.parent.mkdir(parents=True)
    evidence_file.write_text(
        json.dumps({"record_subtype": "shadow_would_be_fill", "shadow_would_be_fill": True})
        + "\n"
        + "{bad json}\n",
        encoding="utf-8",
    )

    out = build_operator_proof_status(repo_root=tmp_path)

    assert out["ok"] is True
    shadow = out["passive_operator_items"][0]
    assert shadow["action_required"] is True
    assert shadow["artifact_status"]["artifact_status"] == "recorded_with_parse_errors"
    assert shadow["artifact_status"]["record_count"] == 1
    assert shadow["artifact_status"]["parse_errors"] == 1


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
