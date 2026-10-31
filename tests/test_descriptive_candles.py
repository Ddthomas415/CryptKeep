"""Invented public candle responses; never fetches or evaluates a strategy."""
from copy import deepcopy
import hashlib
import json
import socket
import subprocess

import pytest

from services.backtest import descriptive_candles as candles
from services.backtest import frozen_signal_bridge as frozen
from services.backtest import shared_cash_research as ledger


H = candles.HOUR


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("candle adapter attempted external work")
    for name in ("socket", "create_connection", "getaddrinfo"):
        monkeypatch.setattr(socket, name, refuse)
    for name in ("Popen", "run", "call", "check_output", "check_call"):
        monkeypatch.setattr(subprocess, name, refuse)


def identity(s="A"):
    return {"product_id": s+"-USD", "base_currency": s, "quote_currency": "USD",
            "identity_evidence_sha256": hashlib.sha256(("invented "+s).encode()).hexdigest()}


def capture(rows=None, received=H+123, product="A-USD", raw=None, status=200):
    return {"product_id": product, "method": "GET",
            "url": "https://api.exchange.coinbase.com/products/" + product + "/candles?granularity=3600",
            "received_at_ms": received, "http_status": status,
            "response_bytes": raw if raw is not None else json.dumps(
                [[0, 90, 110, 100, 105, 500]] if rows is None else rows).encode()}


def run(captures, *, identities=None, start=0, end=H, cutoff=3*H):
    return candles.map_candle_captures(captures, identities={"A": identity()} if identities is None else identities,
        start_ms=start, end_ms=end, as_of_ms=cutoff)


def test_raw_column_order_receipt_hash_and_input_preservation():
    data = [capture()]
    original = deepcopy(data)
    result = run(data)
    record = result["observations"]["A"][0]
    assert result["status"] == "COMPLETE" and not result["scoring_authorized"]
    assert record["row"] == [0, 100, 110, 90, 105, 500]
    assert record["known_at_ms"] == H+123  # Never backdated to H.
    assert record["source_sha256"] == hashlib.sha256(data[0]["response_bytes"]).hexdigest()
    assert data == original and not result["source_authenticity_verified"]


def test_forming_candle_is_not_a_completed_version_or_conflict():
    result = run([capture(received=H-1), capture(received=H, rows=[[0, 90, 112, 100, 106, 550]])])
    assert result["status"] == "COMPLETE"
    assert result["observations"]["A"][0]["known_at_ms"] == H
    assert result["ignored_counts"]["still_forming_at_receipt"] == 1


def test_later_identical_response_keeps_earliest_supplied_receipt():
    result = run([capture(received=2*H), capture(received=H+2), capture(received=H+1)])
    assert result["observations"]["A"][0]["known_at_ms"] == H+1
    assert len(result["capture_evidence"]) == 3


def test_equivalent_numeric_json_spelling_is_not_a_revision():
    result = run([capture(received=H+2),
                  capture(rows=[[0,90.0,110.0,100.0,105.0,500.0]], received=H+1)])
    assert result["status"] == "COMPLETE"
    assert result["observations"]["A"][0]["known_at_ms"] == H+1


def test_response_size_over_documented_candle_count_is_rejected():
    result = run([capture(rows=[[0,90,110,100,105,500]] * 301)])
    assert result["coverage"][0]["capture_errors"] == ["invalid_candle_response_shape"]


def test_completed_revision_is_unknown_not_selected_for_better_results():
    data = [capture(), capture(rows=[[0, 90, 120, 100, 115, 500]], received=2*H)]
    result = run(data)
    assert result["status"] == "INCOMPLETE" and not result["observations"]["A"]
    assert len(result["coverage"][0]["conflicts"][0]["versions"]) == 2
    assert result["coverage"][0]["missing_or_conflicting_hours"] == [0]


def test_future_capture_cannot_repair_or_corrupt_an_earlier_prefix():
    result = run([capture(), capture(raw=b"bad", received=3*H+1)])
    assert result["status"] == "COMPLETE" and result["ignored_counts"]["future_capture"] == 1
    assert run([capture(received=3*H+1)])["status"] == "INCOMPLETE"


def test_future_unrelated_receipt_is_excluded_before_payload_or_route_validation():
    later = capture(received=3*H+1, product="OTHER-USD")
    later["url"] = "https://example.com/irrelevant"
    result = run([capture(), later])
    assert result["status"] == "COMPLETE" and result["ignored_counts"]["future_capture"] == 1


@pytest.mark.parametrize("rows", [[[0, 90, 110, 100, 105]], [[1, 90, 110, 100, 105, 5]],
    [[0, 101, 110, 100, 105, 5]], [[0, 90, 104, 100, 105, 5]],
    [[0, 0, 110, 100, 105, 5]], [[0, 90, 110, 100, 105, -1]],
    [[0, 90, 110, True, 105, 5]], [[0, 90, 110, "100", 105, 5]],
    [[0, 90, 110, 100, 105, 5], [0, 90, 110, 100, 105, 5]]])
def test_bad_rows_are_not_silently_normalized_or_deduplicated(rows):
    result = run([capture(rows=rows)])
    assert result["status"] == "INCOMPLETE" and not result["observations"]["A"]
    assert result["coverage"][0]["capture_errors"]


@pytest.mark.parametrize("raw", [b"bad", b'{}', b'[null]', b'[[0,90,110,100,105,NaN]]', b'\xff'])
def test_unreadable_capture_is_preserved_without_erasing_already_observed_data(raw):
    result = run([capture(), capture(raw=raw, received=2*H)])
    assert result["status"] == "COMPLETE"
    assert result["capture_evidence"][-1]["status"] == "INCOMPLETE"
    assert len(result["observations"]["A"]) == 1
    assert result["coverage"][0]["capture_errors"]


def test_failed_fetch_does_not_invent_an_hour_or_prevent_later_observation():
    result = run([capture(status=500, received=H), capture(received=H+123)])
    assert result["status"] == "COMPLETE"
    assert result["observations"]["A"][0]["known_at_ms"] == H+123
    assert result["coverage"][0]["capture_errors"] == ["http_not_200"]


def test_empty_no_tick_response_is_missing_not_zero_volume_imputation():
    result = run([capture(rows=[])])
    assert result["status"] == "INCOMPLETE" and not result["observations"]["A"]
    assert result["coverage"][0]["missing_or_conflicting_hours"] == [0]


def test_outside_window_rows_are_not_imported():
    result = run([capture(rows=[[0,90,110,100,105,5], [3600,90,110,100,105,5]])])
    assert result["status"] == "COMPLETE" and result["ignored_counts"]["outside_declared_window"] == 1


def test_wrong_product_http_failure_and_future_window_do_not_masquerade_as_data():
    with pytest.raises(ValueError):
        run([capture(product="OTHER-USD")])
    assert run([capture(status=500)])["status"] == "INCOMPLETE"
    with pytest.raises(ValueError):
        run([], end=4*H)


@pytest.mark.parametrize("fault", ["daily", "wrong_host", "wrong_path", "not_get", "missing_url", "duplicate_granularity"])
def test_receipt_cannot_relabel_daily_or_unrelated_data_as_hourly(fault):
    item = capture()
    if fault == "daily":
        item["url"] = item["url"].replace("3600", "86400")
    elif fault == "wrong_host":
        item["url"] = item["url"].replace("api.exchange.coinbase.com", "example.com")
    elif fault == "wrong_path":
        item["url"] = item["url"].replace("A-USD", "B-USD")
    elif fault == "not_get":
        item["method"] = "POST"
    elif fault == "missing_url":
        del item["url"]
    else:
        item["url"] += "&granularity=86400"
    with pytest.raises(ValueError, match="hourly_public_get_receipt_required"):
        run([item])


def test_all_25_symbols_and_unresolved_identity_remain_in_coverage():
    identities = {"TEST%02d" % i: identity("TEST%02d" % i) for i in range(25)}
    identities["TEST24"] = None
    result = run([], identities=identities)
    assert len(result["coverage"]) == len(result["observations"]) == 25
    assert result["coverage"][-1]["capture_errors"] == ["unresolved_identity_evidence"]


def test_actual_panel_rejects_late_receipt_without_rewriting_it():
    data = [capture(received=2*H+1)]
    observations = run(data)["observations"]
    panel = frozen.HourlyPanel(observations)
    with pytest.raises(ledger.Incomplete, match="missing_or_unavailable"):
        panel.window("A", H, 1, available_by_ms=2*H)
    assert panel.window("A", H, 1, available_by_ms=2*H+1) == [[0,100,110,90,105,500]]
