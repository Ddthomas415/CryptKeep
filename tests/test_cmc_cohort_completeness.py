from copy import deepcopy

import pytest

from scripts.research.cmc_cohort_completeness import audit_calendar


def audit(events, observed=("2026-01-01", "2026-01-02")):
    return audit_calendar(events, observed, "2026-01-01", "2026-01-02", "2026-01-02")


def event(name, day="2026-01-01", value=1):
    return {"event_id": name, "utc_day": day, "eligibility": "ELIGIBLE",
            "outcome_status": "AVAILABLE", "excess_return": value}


def test_ratio_preserves_event_weights_and_input():
    events = [event("a"), event("b"), event("c", "2026-01-02", 4)]
    original = deepcopy(events)
    result = audit(events)
    assert result["event_weighted_mean"] == 2
    assert events == original and not result["scoring_authorized"]


def test_true_zero_event_day_stays_on_calendar():
    result = audit([event("a")])
    assert result["calendar"][1]["pair"] == [0, 0]


@pytest.mark.parametrize("eligibility", ["UNKNOWN", "HISTORY_UNCERTAIN"])
def test_unknown_or_unmapped_membership_cannot_become_zero(eligibility):
    row = {"event_id": "x", "utc_day": "2026-01-02", "eligibility": eligibility}
    if eligibility == "HISTORY_UNCERTAIN":
        with pytest.raises(ValueError):
            audit([row])
    else:
        result = audit([row])
        assert result["unknown_events"] == 1
        assert result["calendar"][1]["pair"] is None
        assert result["event_weighted_mean"] is None


def test_missing_list_is_not_zero():
    assert audit([], ("2026-01-01",))["status"] == "INCOMPLETE_FULL_COHORT"


@pytest.mark.parametrize("value", [None, True, float("nan"), float("inf")])
def test_missing_invalid_outcome_refuses(value):
    result = audit([event("a", value=value)])
    assert result["missing_outcomes"] == 1 and result["event_weighted_mean"] is None


def test_immature_window_refuses_and_outside_returns_not_read():
    with pytest.raises(ValueError):
        audit_calendar([], [], "2026-01-01", "2026-01-03", "2026-01-02")
    row = {"event_id": "outside", "utc_day": "2026-01-03"}
    assert audit([row])["event_weighted_mean"] is None


def test_duplicates_refuse():
    with pytest.raises(ValueError, match="duplicate"):
        audit([event("a"), event("a")])


def test_cross_day_sum_overflow_refuses():
    with pytest.raises(ValueError, match="aggregate return sum overflow"):
        audit([event("a", value=1e308), event("b", "2026-01-02", 1e308)])
