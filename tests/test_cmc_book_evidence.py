from copy import deepcopy
from datetime import datetime, timezone
import pytest
from scripts.research.cmc_book_evidence import inspect_book, notional_sensitivity, timing_evidence


def book():
    return {"product_id": "BTC-USD", "request_url": "https://api.exchange.coinbase.com/products/BTC-USD/book?level=1",
            "response": {"response_sha256": "a"*64,
                         "request_started_utc": "2026-10-09T10:00:00Z",
                         "received_utc": "2026-10-09T10:00:01Z",
                         "payload": {"auction_mode": False, "bids": [["100", ".2", 9]],
                                     "asks": [["101", ".1", 4]]}}}


def test_size_is_not_multiplied_by_order_count_or_a_fill():
    record = book(); original = deepcopy(record)
    result = inspect_book(record, "BTC-USD", ".15")
    assert result["status"] == "STRUCTURALLY_VALID"
    assert result["displayed_size_covers_buy"] is False
    assert result["displayed_size_covers_sell"] is True
    assert result["execution"] == "NOT_FILL_PROOF"
    assert result["scoring_authorized"] is False
    assert record == original


@pytest.mark.parametrize("mode", [True, None, "false"])
def test_auction_or_unknown_state_unqualified(mode):
    record = book(); record["response"]["payload"]["auction_mode"] = mode
    assert inspect_book(record, "BTC-USD")["status"] == "UNQUALIFIED_AUCTION_STATE"


@pytest.mark.parametrize("value", [True, "NaN", "Infinity", "0", "-1"])
def test_invalid_sizes_refused(value):
    record = book(); record["response"]["payload"]["asks"][0][1] = value
    assert inspect_book(record, "BTC-USD")["status"] == "INVALID"


def test_wrong_product_and_malformed_times_refused():
    record = book()
    assert inspect_book(record, "ETH-USD")["status"] == "INVALID"
    record["response"]["received_utc"] = "2026-10-09T09:00:00Z"
    assert inspect_book(record, "BTC-USD")["status"] == "INVALID"


@pytest.mark.parametrize("side", ["12", ["12"], [], [[]], [["100"]], {"0": ["100", "1"]}])
def test_malformed_side_and_level_shapes_rejected(side):
    for key in ("bids", "asks"):
        record = book(); record["response"]["payload"][key] = side
        assert inspect_book(record, "BTC-USD")["status"] == "INVALID"


def test_notional_quantity_comes_from_entry_ask_without_fee_or_fill_claim():
    result = notional_sensitivity(book(), "BTC-USD", "101")
    assert result["hypothetical_base_quantity"] == "1"
    assert result["quote_notional_excluding_fees"] == "101"
    assert result["displayed_size_covers_buy"] is False
    assert result["scoring_authorized"] is False


def test_receipt_age_never_becomes_exchange_quote_age():
    record = book()
    record["response"]["payload"]["time"] = "2026-10-09T10:00:02Z"
    original = deepcopy(record)
    result = timing_evidence(record, datetime(2026, 10, 9, 10, 0, 3, tzinfo=timezone.utc))
    assert result["request_duration_seconds"] == 1
    assert result["receipt_age_at_report_seconds"] == 2
    assert result["exchange_quote_age_seconds"] is None
    assert result["scoring_authorized"] is False
    assert result["freshness"] == "UNVERIFIED"
    assert record == original


@pytest.mark.parametrize("value", [None, "bad", "2026-10-09T09:59:59Z",
                                   "2026-10-09T10:01:00Z", "2026-10-09T10:00:01"])
def test_invalid_or_future_receipts_not_qualified(value):
    record = book()
    record["response"]["received_utc"] = value
    result = timing_evidence(record, datetime(2026, 10, 9, 10, 0, 3, tzinfo=timezone.utc))
    assert result["timing_status"] == "INVALID"
    assert result["scoring_authorized"] is False
