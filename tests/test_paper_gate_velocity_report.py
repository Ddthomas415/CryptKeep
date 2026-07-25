from __future__ import annotations

from datetime import datetime, timezone


def test_velocity_refuses_projection_with_less_than_two_closes() -> None:
    from services.control.paper_gate_velocity import compute_round_trip_velocity

    out = compute_round_trip_velocity(
        close_timestamps=["2026-07-09T00:00:00+00:00"],
        recorded=1,
        required=10,
        reference_ts=datetime(2026, 7, 25, tzinfo=timezone.utc),
    )

    assert out["status"] == "insufficient_velocity_history"
    assert out["can_estimate"] is False
    assert out["estimated_completion_ts"] is None


def test_velocity_projects_from_mean_qualified_close_cadence() -> None:
    from services.control.paper_gate_velocity import compute_round_trip_velocity

    out = compute_round_trip_velocity(
        close_timestamps=[
            "2026-06-18T00:00:00+00:00",
            "2026-06-24T00:00:00+00:00",
            "2026-07-09T00:00:00+00:00",
        ],
        recorded=3,
        required=10,
        reference_ts=datetime(2026, 7, 25, tzinfo=timezone.utc),
    )

    assert out["status"] == "projected"
    assert out["qualified_round_trips_remaining"] == 7
    assert out["observed_span_days"] == 21.0
    assert out["mean_days_per_qualified_round_trip"] == 10.5
    assert out["estimated_days_remaining"] == 74
    assert out["estimated_completion_ts"] == "2026-10-07T00:00:00+00:00"


def test_velocity_report_surfaces_legacy_exclusion_and_projection(monkeypatch) -> None:
    from services.control import paper_gate_velocity as velocity

    monkeypatch.setattr(
        velocity,
        "load_paper_promotion_progress",
        lambda: {
            "strategy_id": "es_daily_trend_v1",
            "target_strategy": "sma_200_trend",
            "policy_id": "legacy_round_trip_v1",
            "policy_valid": True,
            "thresholds_ready": False,
            "round_trips_recorded": 3,
            "round_trips_required": 10,
            "round_trips_remaining": 7,
            "all_history_round_trips": 10,
            "days_recorded": 81,
            "days_required": 30,
            "days_remaining": 0,
            "qualified_bars_enabled": False,
            "qualified_bars_recorded": 0,
            "qualified_bars_required": 0,
            "qualified_bars_remaining": 0,
            "qualified_bars_ready": True,
            "bar_count_source": "none",
            "qualification": {
                "completed_round_trip_close_timestamps": [
                    "2026-06-18T00:00:00+00:00",
                    "2026-06-24T00:00:00+00:00",
                    "2026-07-09T00:00:00+00:00",
                ],
            },
            "qualification_explanation": {
                "summary_text": "legacy history excluded",
            },
            "blocking_thresholds": [
                {
                    "label": "10+ completed round trips",
                    "state": "fail",
                    "observed": 3,
                    "required": 10,
                    "remaining": 7,
                }
            ],
        },
    )

    out = velocity.build_paper_gate_velocity_report(
        reference_ts=datetime(2026, 7, 25, tzinfo=timezone.utc)
    )

    assert out["read_only"] is True
    assert out["round_trips"]["excluded_all_history"] == 7
    assert out["velocity"]["estimated_days_remaining"] == 74
    assert any(item["id"] == "legacy_history_excluded" for item in out["findings"])
    assert any(item["id"] == "slow_gate_velocity" for item in out["findings"])
