from datetime import datetime, timedelta, timezone

from scripts.research.cmc_diagnostic_evaluator import evaluate


def quote(time):
    return {"payload": {"bid": "100", "ask": "101"},
            "request_started_utc": time.isoformat(), "received_utc": time.isoformat()}


def inputs():
    time = datetime(2026, 11, 9, tzinfo=timezone.utc)
    event = {"cohort_status": "PRIMARY_COHORT_CANDIDATE", "identity_eligible": True,
             "coin_quote": quote(time), "btc_quote": quote(time)}
    end = {"identity_eligible": True, "coin_quote": quote(time+timedelta(days=7)),
           "btc_quote": quote(time+timedelta(days=7))}
    return event, end


def test_composed_diagnostic_not_scoring():
    event, end = inputs()
    result = evaluate(event, [end], 7)
    assert result["status"] == "DIAGNOSTIC"
    assert result["excess_return"] == 0
    assert result["fee_per_side"] == .012
    assert result["scoring_authorized"] is False
    assert result["freshness"] == "UNVERIFIED"


def test_missing_endpoint_not_invented():
    event, _ = inputs()
    assert evaluate(event, [], 7)["status"] == "MISSING"


def test_uncertain_cohort_and_identity_excluded():
    event, end = inputs(); event["cohort_status"] = "HISTORY_UNCERTAIN"
    assert evaluate(event, [end], 7)["status"] == "EXCLUDED_COHORT"
    event["cohort_status"] = "PRIMARY_COHORT_CANDIDATE"; event["identity_eligible"] = False
    assert evaluate(event, [end], 7)["status"] == "EXCLUDED_IDENTITY"


def test_invalid_endpoint_quote_excluded():
    event, end = inputs(); end["coin_quote"]["payload"]["bid"] = "nan"
    assert evaluate(event, [end], 7)["status"] == "MISSING"


def test_entry_pair_limit_inclusive():
    event, end = inputs()
    base = datetime.fromisoformat(event["coin_quote"]["received_utc"])
    event["btc_quote"] = quote(base+timedelta(seconds=60))
    assert evaluate(event, [end], 7)["status"] == "DIAGNOSTIC"
    event["btc_quote"] = quote(base+timedelta(seconds=60, microseconds=1))
    assert evaluate(event, [end], 7)["status"] == "UNMATCHED_ENTRY_TIMES"


def test_exit_pair_limit_and_negative_offset():
    event, end = inputs()
    base = datetime.fromisoformat(end["coin_quote"]["received_utc"])
    end["btc_quote"] = quote(base-timedelta(seconds=60))
    assert evaluate(event, [end], 7)["status"] == "DIAGNOSTIC"
    end["btc_quote"] = quote(base-timedelta(seconds=61))
    assert evaluate(event, [end], 7)["status"] == "MISSING"
