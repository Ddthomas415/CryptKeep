from datetime import date, timedelta

from scripts.research.cmc_cohort_coverage import classify_appearance

DAY = date(2026, 11, 9)


def history():
    return {DAY-timedelta(days=n): set() for n in range(31)}


def test_complete_history_is_candidate_not_scoring_authority():
    days = history(); days[DAY] = {42}
    result = classify_appearance(DAY, "42", days)
    assert result["status"] == "PRIMARY_COHORT_CANDIDATE"
    assert result["scoring_authorized"] is False


def test_startup_and_gap_are_uncertain():
    assert classify_appearance(DAY, 42, {DAY: {42}})["status"] == "HISTORY_UNCERTAIN"
    days = history(); days[DAY] = {42}; del days[DAY-timedelta(days=30)]
    assert len(classify_appearance(DAY, 42, days)["missing_days"]) == 1


def test_prior_appearance_is_repeat_even_with_gap():
    days = {DAY: {42}, DAY-timedelta(days=30): {"42"}}
    assert classify_appearance(DAY, 42, days)["status"] == "REPEAT_APPEARANCE"


def test_outside_window_does_not_block_candidate():
    days = history(); days[DAY] = {42}; days[DAY-timedelta(days=31)] = {42}
    assert classify_appearance(DAY, 42, days)["status"] == "PRIMARY_COHORT_CANDIDATE"


def test_unobserved_is_not_event():
    assert classify_appearance(DAY, 42, history())["status"] == "NOT_OBSERVED"
