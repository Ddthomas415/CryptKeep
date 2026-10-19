from datetime import date, datetime, timedelta, timezone

import pytest

from scripts.research.cmc_completeness_adapter import audit_cohorts as raw_audit


def audit_cohorts(cohort, outcomes, qualifications, now):
    end = (now-timedelta(days=7, hours=12)).date()-timedelta(days=1)
    return raw_audit(cohort, outcomes, qualifications, now,
                     start_day="2026-01-31", end_day=min(end, date(2026, 1, 31)).isoformat())


def fixture(status="PRIMARY_COHORT_CANDIDATE"):
    days = [(date(2026, 1, 1)+timedelta(days=i)).isoformat() for i in range(31)]
    event = {"utc_day": days[-1], "cmc_id": "1", "cohort_status": status,
             "identity_eligible_at_first_observation": True, "first_snapshot_sha256": "hash"}
    outcome = {"utc_day": days[-1], "cmc_id": "1", "horizon_days": 7,
               "source_sha256": "hash", "status": "DIAGNOSTIC", "excess_return": .2}
    qualification = {"utc_day": days[-1], "cmc_id": "1", "horizon_days": 7, "qualified": True,
                     "entry": {"status": "QUALIFIED"}, "exit": {"status": "QUALIFIED"}}
    return {"observed_utc_days": days, "events": [event]}, [outcome], [qualification]


NOW = datetime(2026, 2, 10, tzinfo=timezone.utc)


def test_available_qualified_event_preserves_mean():
    result = audit_cohorts(*fixture(), NOW)
    assert result["status"] == "COMPLETE_FULL_COHORT"
    assert result["event_weighted_mean"] == .2
    assert not result["scoring_authorized"]


@pytest.mark.parametrize("status", ["HISTORY_UNCERTAIN", "AMBIGUOUS_FIRST_CAPTURE", "NOT_OBSERVED"])
def test_unknown_membership_stays_unknown(status):
    result = audit_cohorts(*fixture(status), NOW)
    assert result["unknown_events"] == 1 and result["calendar"][0]["pair"] is None


def test_repeat_is_known_excluded():
    result = audit_cohorts(*fixture("REPEAT_APPEARANCE"), NOW)
    assert result["calendar"][0]["pair"] == [0, 0]


def test_unqualified_exit_stays_missing_not_excluded():
    cohort, outcomes, qualified = fixture()
    qualified[0]["qualified"] = False
    result = audit_cohorts(cohort, outcomes, qualified, NOW)
    assert result["eligible_events"] == 1 and result["missing_outcomes"] == 1


def test_immature_day_return_not_accessed():
    cohort, outcomes, qualified = fixture()
    del outcomes[0]["excess_return"]
    assert audit_cohorts(cohort, outcomes, qualified, datetime(2026, 2, 1, tzinfo=timezone.utc))["status"] == "NO_MATURE_PRIMARY_WINDOW"


def test_duplicate_and_source_mismatch_refuse():
    cohort, outcomes, qualified = fixture()
    with pytest.raises(ValueError, match="duplicate"):
        audit_cohorts(cohort, outcomes*2, qualified, NOW)
    outcomes[0]["source_sha256"] = "wrong"
    with pytest.raises(ValueError, match="source mismatch"):
        audit_cohorts(cohort, outcomes, qualified, NOW)


def test_missing_trailing_day_does_not_shrink_declared_window():
    result = raw_audit(*fixture(), NOW, start_day="2026-01-31", end_day="2026-02-01")
    assert result["status"] == "INCOMPLETE_FULL_COHORT"
    assert result["calendar"][-1]["day"] == "2026-02-01"
    assert result["calendar"][-1]["pair"] is None


def test_fixed_entry_qualification_exclusion_is_not_missing_exit():
    cohort, outcomes, qualified = fixture()
    qualified[0].update(qualified=False, entry={"status": "EXCLUDED", "reasons": ["STALE"]})
    result = audit_cohorts(cohort, outcomes, qualified, NOW)
    assert result["eligible_events"] == result["missing_outcomes"] == 0
    assert result["entry_rule_exclusions"][0]["reasons"] == ["STALE"]


def test_wrapper_exit_linkage_failure_preserves_valid_entry(monkeypatch, tmp_path):
    from scripts.research import run_cmc_qualified_report as wrapper
    from scripts.research import cmc_daily_cohorts
    cohort, outcomes, _ = fixture()
    envelope = {"file": "source", "sha256": "hash",
                "snapshot_utc": datetime(2026, 1, 31, tzinfo=timezone.utc),
                "data": {"trending_hidden_boost": [{"type": "listing", "cmc_id": "1",
                          "coinbase_product": "X-USD", "identity_eligible": True, "coinbase": {}}]}}
    report = {"as_of_utc": "2026-02-09T00:00:00+00:00",
              "source_files": [{"file": "source", "sha256": "hash"}],
              "outcomes": outcomes, "statistics": {"status": "NOT_READY_90_DAYS"},
              "observed_utc_days": cohort["observed_utc_days"],
              "status_counts": {"DIAGNOSTIC": 1}, "rejected_envelopes": []}
    monkeypatch.setattr(wrapper, "run", lambda *_: report)
    monkeypatch.setattr(wrapper, "load_snapshot", lambda *_: envelope)
    monkeypatch.setattr(cmc_daily_cohorts, "build_cohorts", lambda *_: cohort)
    monkeypatch.setattr(wrapper, "qualify_capture", lambda *a, **k:
                        {"status": "QUALIFIED", "quantity": 1, "reasons": [], "flags": []})
    def missing(*_):
        raise StopIteration("missing endpoint")
    monkeypatch.setattr(wrapper, "_endpoint", missing)
    result = wrapper.run_qualified(tmp_path, datetime(2026, 2, 9, tzinfo=timezone.utc))
    assert result["qualification_rows"][0]["entry"]["status"] == "QUALIFIED"
    assert result["cohort_completeness"]["missing_outcomes"] == 1
    assert result["cohort_completeness"]["status"] == "INCOMPLETE_FULL_COHORT"
