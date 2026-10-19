import copy
from datetime import date, timedelta

import numpy as np
import pytest

from scripts.research.cmc_cohort_completeness import audit_calendar
from scripts.research import cmc_paired_ratio_candidate as candidate


def audit(n=90, constant=False):
    days = [(date(2027, 1, 1) + timedelta(days=i)).isoformat() for i in range(n)]
    events = [{"utc_day": day, "event_id": f"{i}-{j}",
               "eligibility": "ELIGIBLE", "outcome_status": "AVAILABLE",
               "excess_return": .01 if constant else (i % 11 - 5) / 100}
              for i, day in enumerate(days) for j in range(1 + i % 3)]
    return audit_calendar(events, days, days[0], days[-1], days[-1])


def test_reproducible_paired_event_mean_and_no_mutation():
    data = audit()
    original = copy.deepcopy(data)
    result = candidate.candidate_interval(data, seed=123)
    assert result == candidate.candidate_interval(data, seed=123)
    assert result["status"] == "CANDIDATE_INTERVAL"
    assert result["event_weighted_mean"] == data["event_weighted_mean"]
    assert result["scoring_authorized"] is False
    assert result["completed_replicates"] == 2000
    assert data == original


def test_exact_cube_root():
    for n, expected in [(90, 7), (343, 7), (344, 8), (512, 8), (513, 9)]:
        assert candidate.block_length(n) == expected


def test_circular_pairs_and_truncation():
    class LastStart:
        def integers(self, low, high, size):
            assert (low, high, size) == (0, 10, 2)
            return [9, 9]
    pairs = [[i, i + 1] for i in range(10)]
    drawn = candidate.sample_pairs(pairs, LastStart(), 7)
    assert drawn == [pairs[i] for i in [9, 0, 1, 2, 3, 4, 5, 9, 0, 1]]


@pytest.mark.parametrize("seed", [True, -1, 1.5, "1"])
def test_invalid_seed(seed):
    with pytest.raises(ValueError):
        candidate.candidate_interval(audit(), seed=seed)


@pytest.mark.parametrize("damage", ["missing", "gap", "unknown", "count", "nan", "boolean", "mean"])
def test_refuses_invalid_input(damage):
    data = audit()
    if damage == "missing": data["status"] = "INCOMPLETE_FULL_COHORT"
    if damage == "gap": data["calendar"].pop(2)
    if damage == "unknown": data["calendar"][0]["unknown"] = 1
    if damage == "count": data["eligible_events"] += 1
    if damage == "nan": data["calendar"][0]["pair"][0] = float("nan")
    if damage == "boolean": data["calendar"][0]["pair"][1] = True
    if damage == "mean": data["event_weighted_mean"] += 1
    with pytest.raises(ValueError):
        candidate.candidate_interval(data, seed=1)


def test_zero_event_day_is_valid():
    data = audit()
    row = data["calendar"][2]
    data["eligible_events"] -= row["eligible"]
    row.update(pair=[0, 0], eligible=0)
    data["event_weighted_mean"] = candidate._ratio([r["pair"] for r in data["calendar"]])
    assert candidate.candidate_interval(data, seed=1)["status"] == "CANDIDATE_INTERVAL"


def test_zero_denominator_refuses_whole_interval(monkeypatch):
    monkeypatch.setattr(candidate, "sample_pairs", lambda *args: [[0, 0]] * 90)
    result = candidate.candidate_interval(audit(), seed=1)
    assert result["status"] == "INCOMPLETE"
    assert result["interval"] is None
    assert result["completed_replicates"] == 0


def test_basic_interval_sign_and_indices(monkeypatch):
    data = audit()
    estimate = data["event_weighted_mean"]
    iterator = iter(range(2000))
    monkeypatch.setattr(candidate, "sample_pairs",
                        lambda *args: [[estimate + next(iterator), 1]])
    result = candidate.candidate_interval(data, seed=1)
    assert result["interval"] == [estimate - 1900, estimate - 100]


def test_degenerate_not_positive(monkeypatch):
    data = audit()
    monkeypatch.setattr(candidate, "sample_pairs", lambda pairs, *args: pairs)
    assert candidate.candidate_interval(data, seed=1)["status"] == "DEGENERATE"


def test_too_few_days():
    with pytest.raises(ValueError, match="blocks"):
        candidate.candidate_interval(audit(n=13), seed=1)


@pytest.mark.parametrize("key,value", [("eligible", True), ("eligible", 1.0),
    ("unknown", False), ("missing_outcomes", False), ("excluded", False)])
def test_strict_daily_count_metadata(key, value):
    data = audit()
    data["calendar"][0][key] = value
    with pytest.raises(ValueError, match="count metadata"):
        candidate.candidate_interval(data, seed=1)


@pytest.mark.parametrize("key,value", [("eligible_events", 180.0),
    ("eligible_events", True), ("event_weighted_mean", False),
    ("event_weighted_mean", float("inf")), ("event_weighted_mean", 10**1000)])
def test_strict_aggregate_metadata(key, value):
    data = audit()
    data[key] = value
    with pytest.raises(ValueError, match="aggregate metadata"):
        candidate.candidate_interval(data, seed=1)
