import pytest

from scripts.research.cmc_quote_evidence import inspect_quote


def quote():
    return {"payload": {"bid": "100", "ask": "101", "time": "old-trade-time"},
            "request_started_utc": "2026-10-09T05:00:00Z",
            "received_utc": "2026-10-09T05:00:01Z"}


def test_structural_validity_does_not_authorize_freshness():
    result = inspect_quote(quote())
    assert result["status"] == "STRUCTURALLY_VALID"
    assert result["freshness"] == "UNVERIFIED"
    assert result["execution"] == "NOT_FILL_PROOF"
    assert result["capture_seconds"] == 1


@pytest.mark.parametrize("bid,ask", [(True, 2), (0, 1), (2, 1), ("nan", 1), (1, "inf"), (None, 1)])
def test_invalid_prices(bid, ask):
    record = quote()
    record["payload"].update(bid=bid, ask=ask)
    assert inspect_quote(record)["status"] == "INVALID"


@pytest.mark.parametrize("time", ["2026-10-09T04:59:59Z", "2026-10-09T05:00:01", "bad"])
def test_invalid_receipt(time):
    record = quote()
    record["received_utc"] = time
    assert inspect_quote(record)["status"] == "INVALID"


def test_missing_and_error_records():
    assert inspect_quote({})["status"] == "INVALID"
    record = quote()
    record["error"] = "timeout"
    assert inspect_quote(record)["status"] == "INVALID"
