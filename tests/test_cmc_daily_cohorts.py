from datetime import datetime, timedelta, timezone

from scripts.research.cmc_daily_cohorts import build_cohorts
import pytest


def snapshot(time, coin=42, eligible=False):
    return {"snapshot_utc": time, "file": time.isoformat(), "sha256": "hash",
            "data": {"trending_status": "OBSERVED", "source_errors": [],
                     "trending_hidden_boost": [{"type": "listing", "cmc_id": coin, "identity_eligible": eligible}]}}


def test_later_identity_does_not_upgrade_first_or_double_count():
    time = datetime(2026, 10, 9, tzinfo=timezone.utc)
    result = build_cohorts([snapshot(time), snapshot(time+timedelta(hours=1), eligible=True)])
    assert len(result["events"]) == 1
    assert result["events"][0]["identity_eligible_at_first_observation"] is False
    assert result["events"][0]["cohort_status"] == "HISTORY_UNCERTAIN"


def test_full_prior_coverage_and_union_presence():
    time = datetime(2026, 11, 9, tzinfo=timezone.utc)
    rows = [snapshot(time-timedelta(days=n), coin=7) for n in range(1,31)]
    rows.append(snapshot(time, eligible=True))
    result = build_cohorts(rows)
    event = next(item for item in result["events"] if item["cmc_id"] == "42")
    assert event["cohort_status"] == "PRIMARY_COHORT_CANDIDATE"


def test_invalid_list_cannot_prove_coverage():
    time = datetime(2026, 10, 9, tzinfo=timezone.utc)
    evidence = snapshot(time); evidence["data"]["trending_hidden_boost"] *= 2
    result = build_cohorts([evidence])
    assert result["observed_utc_days"] == []
    assert len(result["excluded_lists"]) == 1


@pytest.mark.parametrize("coin", ["\u00b2", "\u0661", True, 0, -1, None])
def test_malformed_id_excluded_without_abort(coin):
    time = datetime(2026, 10, 9, tzinfo=timezone.utc)
    result = build_cohorts([snapshot(time, coin=coin)])
    assert result["events"] == []
    assert len(result["excluded_lists"]) == 1


def test_dex_context_does_not_invalidate_listed_coverage():
    time = datetime(2026, 10, 9, tzinfo=timezone.utc)
    evidence = snapshot(time)
    evidence["data"]["trending_hidden_boost"].append({"type": "dex", "cmc_id": None})
    result = build_cohorts([evidence])
    assert len(result["events"]) == 1
    assert result["excluded_context"][0]["dex_rows_outside_listed_event_scope"] == 1


def test_conflicting_equal_time_capture_excluded_not_filename_selected():
    time = datetime(2026, 10, 9, tzinfo=timezone.utc)
    a, b = snapshot(time), snapshot(time, eligible=True)
    a["file"], b["file"] = "a", "b"
    result = build_cohorts([b, a])
    assert result["events"][0]["cohort_status"] == "AMBIGUOUS_FIRST_CAPTURE"
    assert len(result["observed_utc_days"]) == 1


def test_identical_equal_time_capture_does_not_create_new_event():
    time = datetime(2026, 10, 9, tzinfo=timezone.utc)
    a, b = snapshot(time), snapshot(time)
    a["file"], b["file"] = "a", "b"
    assert len(build_cohorts([a,b])["events"]) == 1
