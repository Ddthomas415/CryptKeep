from __future__ import annotations

from dashboard.services.promotion_ladder import build_promotion_readiness


class _Decision:
    def __init__(self, *, ok: bool) -> None:
        self.ok = ok


def test_promotion_readiness_blocks_paper_to_sandbox_on_thin_evidence() -> None:
    out = build_promotion_readiness(
        as_of="2026-03-19T12:00:00Z",
        runtime_context={
            "mode_value": "paper",
            "normalized_live_enabled": False,
            "kill_armed": False,
        },
        leaderboard_summary={
            "rows": [
                {
                    "name": "Breakout Default",
                    "recommendation": "keep",
                    "closed_trades": 1,
                    "post_cost_return_pct": 12.0,
                }
            ]
        },
        structural_health={"needs_attention": False},
        collector_runtime={"freshness": "Fresh", "errors": 0},
    )

    assert out["current_stage_label"] == "Paper"
    assert out["target_stage_label"] == "Sandbox Live"
    assert out["status"] == "warn"
    assert any("execution.live_enabled remains false" in item for item in out["blockers"])
    assert any("require at least 3" in item for item in out["blockers"])


def test_promotion_readiness_allows_sandbox_to_tiny_live_review_when_criteria_clear() -> None:
    out = build_promotion_readiness(
        as_of="2026-03-19T12:00:00Z",
        runtime_context={
            "mode_value": "sandbox_live",
            "normalized_live_enabled": True,
            "guard_allowed": True,
            "armed": True,
            "kill_armed": False,
            "start_decision": _Decision(ok=True),
        },
        leaderboard_summary={
            "rows": [
                {
                    "name": "Breakout Default",
                    "recommendation": "keep",
                    "closed_trades": 6,
                    "max_drawdown_pct": 4.2,
                    "paper_live_drift": "low",
                }
            ]
        },
        structural_health={"needs_attention": False},
        collector_runtime={"freshness": "Fresh", "errors": 0},
    )

    assert out["current_stage_label"] == "Sandbox Live"
    assert out["target_stage_label"] == "Tiny Live"
    assert out["status"] == "ok"
    assert out["blockers"] == []


def test_promotion_readiness_blocks_when_only_synthetic_fallback_truth_exists() -> None:
    out = build_promotion_readiness(
        as_of="2026-03-19T12:00:00Z",
        runtime_context={
            "mode_value": "paper",
            "normalized_live_enabled": True,
            "kill_armed": False,
        },
        leaderboard_summary={
            "rows": [
                {
                    "name": "Breakout Default",
                    "recommendation": "keep",
                    "closed_trades": 4,
                    "post_cost_return_pct": 12.0,
                }
            ]
        },
        structural_health={"needs_attention": False},
        collector_runtime={"freshness": "Fresh", "errors": 0},
        strategy_truth={
            "truth_source": "synthetic_fallback",
            "freshness_status": "missing",
            "caveat": "Persisted strategy evidence artifact is unavailable; digest is using labeled synthetic fallback built on demand.",
        },
    )

    assert out["status"] == "warn"
    assert any("synthetic fallback" in item.lower() for item in out["blockers"])
