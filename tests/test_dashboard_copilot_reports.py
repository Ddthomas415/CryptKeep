from __future__ import annotations

import json

from dashboard.services.copilot_reports import (
    build_copilot_report_focus,
    list_copilot_reports,
    load_copilot_report_bundle,
    summarize_copilot_reports,
)


def test_list_copilot_reports_classifies_and_sorts(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    reports_dir = tmp_path / "runtime" / "ai_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    (reports_dir / "review.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-04-08T01:00:00+00:00",
                "risk_tier": "yellow",
                "changed_files": ["services/ai_copilot/policy.py"],
                "summary": "Repo review.",
            }
        ),
        encoding="utf-8",
    )
    (reports_dir / "lab.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-04-08T02:00:00+00:00",
                "severity": "ok",
                "selected_strategy": "ema_cross",
                "top_rows": [],
                "summary": "Strategy lab.",
            }
        ),
        encoding="utf-8",
    )
    (reports_dir / "lab.md").write_text("# Strategy Lab\n", encoding="utf-8")

    rows = list_copilot_reports(limit=10)

    assert rows[0]["stem"] == "lab"
    assert rows[0]["kind"] == "strategy_lab"
    assert rows[1]["kind"] == "repo_review"

    overview = summarize_copilot_reports(limit=10)
    assert overview["report_count"] == 2
    assert overview["kind_counts"]["strategy_lab"] == 1


def test_load_copilot_report_bundle_reads_markdown(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    reports_dir = tmp_path / "runtime" / "ai_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    (reports_dir / "safety.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-04-08T03:00:00+00:00",
                "severity": "warn",
                "runtime": {"live_allowed": False},
                "place_order_contract": {"has_enforce_fail_closed": True},
                "summary": "Safety warning.",
            }
        ),
        encoding="utf-8",
    )
    (reports_dir / "safety.md").write_text("# Safety Audit\nwarn\n", encoding="utf-8")

    bundle = load_copilot_report_bundle("safety")

    assert bundle["kind"] == "safety_audit"
    assert bundle["payload"]["severity"] == "warn"
    assert "# Safety Audit" in bundle["markdown"]


def test_build_copilot_report_focus_marks_strategy_lab_warning_with_runtime_detail() -> None:
    focus = build_copilot_report_focus(
        kind="strategy_lab",
        severity="warn",
        payload={
            "summary": "Strategy lab report is based on partial evidence.",
            "collector_runtime": {
                "status": "stopped",
                "completed_strategies": 1,
                "total_strategies": 3,
                "summary_text": "Paper evidence collector is stopped (1/3 complete).",
            },
            "research_acceptance": {
                "accepted": False,
                "status": "not_accepted",
                "summary": "`breakout_donchian` does not meet the current research-acceptance floor yet.",
                "blockers": [
                    "Current evidence cycle is partial at 1/3 completed strategies.",
                    "Persisted paper history only has 1 closed trade(s); the current research floor requires 30.",
                ],
            },
            "walk_forward": {
                "available": True,
                "status": "ok",
                "research_only": True,
                "bars": 240,
                "window_count": 4,
                "summary": {
                    "avg_test_return_pct": 1.6,
                    "avg_test_max_drawdown_pct": 2.3,
                    "non_negative_test_window_ratio": 0.75,
                    "total_test_trades": 10,
                    "total_test_closed_trades": 5,
                },
            },
        },
    )

    assert focus["tone"] == "warning"
    assert "partial evidence" in focus["message"]
    assert "1/3 complete" in focus["message"]
    assert focus["details"]["completed_strategies"] == 1
    assert focus["details"]["research_acceptance_status"] == "not_accepted"
    assert focus["details"]["research_acceptance_accepted"] is False
    assert "research-acceptance floor" in focus["details"]["research_acceptance_summary"]
    assert len(focus["details"]["research_acceptance_blockers"]) == 2
    assert focus["details"]["walk_forward_available"] is True
    assert focus["details"]["walk_forward_status"] == "ok"
    assert focus["details"]["walk_forward_window_count"] == 4
    assert focus["details"]["walk_forward_summary"]["avg_test_return_pct"] == 1.6
