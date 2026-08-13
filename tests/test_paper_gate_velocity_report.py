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


def test_qualified_bar_velocity_projects_from_unique_bar_cadence() -> None:
    from services.control.paper_gate_velocity import compute_qualified_bar_velocity

    out = compute_qualified_bar_velocity(
        bar_timestamps=[
            "2026-07-01",
            "2026-07-02",
            "2026-07-03",
            "2026-07-04",
        ],
        recorded=4,
        required=7,
        reference_ts=datetime(2026, 7, 10, tzinfo=timezone.utc),
    )

    assert out["status"] == "projected"
    assert out["qualified_bars_remaining"] == 3
    assert out["observed_span_days"] == 3.0
    assert out["mean_days_per_qualified_bar"] == 1.0
    assert out["estimated_days_remaining"] == 3
    assert out["estimated_completion_ts"] == "2026-07-13T00:00:00+00:00"


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
            "qualified_bar_timestamps": [],
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


def test_velocity_report_overall_estimate_uses_latest_incomplete_threshold(monkeypatch) -> None:
    from services.control import paper_gate_velocity as velocity

    monkeypatch.setattr(
        velocity,
        "load_paper_promotion_progress",
        lambda: {
            "strategy_id": "es_daily_trend_v1",
            "target_strategy": "sma_200_trend",
            "policy_id": "slow_daily_single_symbol_v1",
            "policy_valid": True,
            "thresholds_ready": False,
            "round_trips_recorded": 3,
            "round_trips_required": 5,
            "round_trips_remaining": 2,
            "all_history_round_trips": 10,
            "days_recorded": 95,
            "days_required": 45,
            "days_remaining": 0,
            "qualified_bars_enabled": True,
            "qualified_bars_recorded": 47,
            "qualified_bars_required": 60,
            "qualified_bars_remaining": 13,
            "qualified_bars_ready": False,
            "bar_count_source": "legacy_signal_date",
            "qualified_bar_timestamps": [
                "2026-06-16",
                "2026-06-17",
                "2026-06-18",
                "2026-06-19",
            ],
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
                    "label": "5+ completed round trips",
                    "state": "fail",
                    "observed": 3,
                    "required": 5,
                    "remaining": 2,
                },
                {
                    "label": "60+ qualified source bars",
                    "state": "fail",
                    "observed": 47,
                    "required": 60,
                    "remaining": 13,
                },
            ],
        },
    )

    out = velocity.build_paper_gate_velocity_report(
        reference_ts=datetime(2026, 8, 8, tzinfo=timezone.utc)
    )

    assert out["velocity"]["estimated_days_remaining"] == 21
    assert out["qualified_bar_velocity"]["estimated_days_remaining"] == 13
    assert out["overall_velocity"] == {
        "status": "projected",
        "can_estimate": True,
        "estimated_days_remaining": 21,
        "estimated_completion_ts": "2026-08-29T00:00:00+00:00",
        "blocking_threshold": "round_trips",
        "reason": "latest_projected_incomplete_threshold",
    }
    assert "Overall projected completion is governed by round_trips" in out["summary_text"]


def test_velocity_report_writer_records_latest_and_stamped_json(tmp_path) -> None:
    from services.control.paper_gate_velocity import write_paper_gate_velocity_artifact

    report = {
        "ok": True,
        "read_only": True,
        "report_type": "paper_gate_velocity",
        "strategy_id": "es_daily_trend_v1",
        "round_trips": {"qualified": 3},
        "qualified_bars": {"recorded": 47},
    }

    paths = write_paper_gate_velocity_artifact(report, evidence_dest=tmp_path)

    latest = tmp_path / "paper_gate_velocity.latest.json"
    assert paths["latest_json"] == str(latest)
    assert latest.exists()
    stamped = list(tmp_path.glob("paper_gate_velocity.*.json"))
    assert len(stamped) == 2  # latest + timestamped
