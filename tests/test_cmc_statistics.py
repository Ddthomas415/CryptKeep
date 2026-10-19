from datetime import date, timedelta

from scripts.research.cmc_statistics import summarize


def test_not_ready_never_scores():
    assert summarize([], [], False)["status"] == "NOT_READY_90_DAYS"


def test_missing_outcomes_visible_without_changing_return_mean():
    days = ["2026-11-01", "2026-11-02"]
    rows = [{"status": "DIAGNOSTIC", "horizon_days": 7, "utc_day": day,
             "excess_return": .02} for day in days]
    rows += [{"status": "MISSING", "horizon_days": 7} for _ in range(18)]
    rows += [{"status": "IMMATURE", "horizon_days": 7},
             {"status": "EXCLUDED_IDENTITY"},
             {"status": "MISSING", "horizon_days": 30}]
    result = summarize(rows, days, True, repeats=100)
    assert result["coverage"]["seven_day_records"] == 21
    assert result["coverage"]["available_seven_day_returns"] == 2
    assert result["coverage"]["unavailable_seven_day_returns"] == 19
    assert result["coverage"]["seven_day_status_counts"] == {"DIAGNOSTIC": 2, "MISSING": 18, "IMMATURE": 1}
    assert result["coverage"]["pre_horizon_exclusions"] == {"EXCLUDED_IDENTITY": 1}
    assert result["mean_excess_return"] == .02


def test_coverage_present_before_readiness_and_with_insufficient_days():
    rows = [{"status": "MISSING", "horizon_days": 7}]
    for ready in (False, True):
        result = summarize(rows, [], ready)
        assert result["coverage"]["unavailable_seven_day_returns"] == 1
        assert result["scoring_authorized"] is False


def test_same_day_events_remain_clustered():
    days = [(date(2026,11,1)+timedelta(days=i)).isoformat() for i in range(90)]
    outcomes = [{"status": "DIAGNOSTIC", "horizon_days": 7, "utc_day": day,
                 "excess_return": .02} for day in days for _ in range(2)]
    result = summarize(outcomes, days, True, repeats=100)
    assert result["events"] == 180
    assert result["entry_days"] == 90
    assert abs(result["registered_entry_day_bootstrap"]["p05"]-.02) < 1e-12
    assert result["scoring_authorized"] is False


def test_missing_days_refuse_serial_sensitivity():
    days = ["2026-11-01", "2026-11-03"]
    outcomes = [{"status": "DIAGNOSTIC", "horizon_days": 7, "utc_day": day,
                 "excess_return": value} for day,value in zip(days,[.1,-.1])]
    result = summarize(outcomes, days, True, repeats=100)
    assert result["serial_dependence_sensitivities_not_replacement_gate"]["7"]["status"] == "MISSING_CALENDAR_COVERAGE"
