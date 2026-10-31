from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import socket
import sqlite3

import pytest

from scripts.research.synthetic_okx_funding_contract import describe_okx_funding_pair


BASE = int(datetime(2026, 10, 29, tzinfo=timezone.utc).timestamp() * 1000)
HOUR = 3600000


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("network/database boundary forbidden")
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(sqlite3, "connect", refuse)


def inputs(interval=8):
    current = {"instId": "BTC-USDT-SWAP", "instType": "SWAP", "fundingRate": "0.0002",
               "settFundingRate": "0.0001", "nextFundingRate": "", "settState": "settled",
               "prevFundingTime": str(BASE), "fundingTime": str(BASE + interval * HOUR),
               "nextFundingTime": str(BASE + interval * HOUR * 2), "formulaType": "withRate"}
    history = [{"instId": "BTC-USDT-SWAP", "instType": "SWAP", "fundingRate": "0.9",
                "realizedRate": "0.0001", "fundingTime": str(BASE - n * interval * HOUR)}
               for n in range(3)]
    return wrap(current, history)


def wrap(current, history):
    result = {"requested_inst_id": "BTC-USDT-SWAP"}
    for name, data, endpoint in (("current", [current], "funding-rate"),
                                 ("history", history, "funding-rate-history")):
        body = json.dumps({"code": "0", "data": data}).encode()
        result[name + "_body"] = body
        result[name + "_receipt"] = receipt(body, endpoint)
    return result


def receipt(body, endpoint):
    return {"url": "https://www.okx.com/api/v5/public/" + endpoint
            + "?instId=BTC-USDT-SWAP" + ("&limit=5" if endpoint.endswith("history") else ""),
            "curl_exit_code": 0, "http_status": "200", "body_bytes": len(body),
            "body_sha256": hashlib.sha256(body).hexdigest(),
            "request_started_at": "2026-10-29T00:00:01Z", "received_at": "2026-10-29T00:00:02Z"}


def change_payload(args, name, edit):
    payload = json.loads(args[name + "_body"])
    edit(payload)
    body = json.dumps(payload).encode()
    args[name + "_body"] = body
    args[name + "_receipt"] = receipt(body, "funding-rate" + ("-history" if name == "history" else ""))


def denied(out):
    assert out["normalization_eligible"] is False
    assert out["strategy_eligible"] is False
    assert out["execution_authority"] is False
    assert out["annualized_pct"] is None and out["rate_per_8h"] is None


@pytest.mark.parametrize("interval", [1, 2, 4, 8, 16])
def test_fields_remain_distinct_and_observed_gaps_do_not_qualify(interval):
    args = inputs(interval)
    original = deepcopy(args)
    out = describe_okx_funding_pair(**args)
    assert args == original
    assert out["current"]["decimal_rate"] == "0.0002"
    assert out["current"]["kind"] == "current_unsettled_or_estimate"
    assert out["reported_settlement"]["decimal_rate"] == "0.0001"
    assert out["next"]["decimal_rate"] is None
    assert out["scheduled_gap_hours"] == str(interval)
    assert [row["preceding_observed_gap_hours"] for row in out["history"]] == [None, str(interval), str(interval)]
    assert all(row["effective_interval_verified"] is False for row in out["history"])
    assert out["history"][-1]["published"]["decimal_rate"] == "0.9"
    assert out["history"][-1]["realized"]["decimal_rate"] == "0.0001"
    assert out["cross_checks"]["reported_settled_rate_matches_history"] is True
    denied(out)


@pytest.mark.parametrize("value", [None, "", "nan", "Infinity", "bad", True, 0.01])
def test_unknown_realized_rate_never_falls_back_to_published_rate(value):
    args = inputs()
    change_payload(args, "history", lambda p: p["data"][0].update(realizedRate=value))
    out = describe_okx_funding_pair(**args)
    assert out["history"][-1]["realized"]["decimal_rate"] is None
    assert out["cross_checks"]["reported_settled_rate_matches_history"] is None
    denied(out)


@pytest.mark.parametrize("value", ["0", "-0.0002", "0.00010000000000000000000001"])
def test_exact_finite_signed_and_zero_rates_are_preserved(value):
    args = inputs()
    change_payload(args, "current", lambda p: p["data"][0].update(settFundingRate=value))
    change_payload(args, "history", lambda p: p["data"][0].update(realizedRate=value))
    out = describe_okx_funding_pair(**args)
    assert out["reported_settlement"]["decimal_rate"] == value
    assert out["cross_checks"]["reported_settled_rate_matches_history"] is True
    denied(out)


@pytest.mark.parametrize("state", [None, "settling", "", "unknown"])
def test_unsettled_status_does_not_certify_even_matching_rates(state):
    args = inputs()
    change_payload(args, "current", lambda p: p["data"][0].update(settState=state))
    out = describe_okx_funding_pair(**args)
    assert out["reported_settlement"]["reported_settled"] is False
    assert out["cross_checks"]["reported_settled_rate_matches_history"] is None
    denied(out)


def test_mismatched_settlement_is_visible_not_repaired():
    args = inputs()
    change_payload(args, "current", lambda p: p["data"][0].update(settFundingRate="0.5"))
    out = describe_okx_funding_pair(**args)
    assert out["cross_checks"]["reported_settled_rate_matches_history"] is False
    denied(out)


def test_missing_previous_event_does_not_borrow_another_history_event():
    args = inputs()
    change_payload(args, "current", lambda p: p["data"][0].update(prevFundingTime=str(BASE - HOUR)))
    out = describe_okx_funding_pair(**args)
    assert out["cross_checks"]["previous_time_in_history"] is False
    assert out["cross_checks"]["reported_settled_rate_matches_history"] is None
    denied(out)


def test_gap_with_a_missing_event_is_only_an_observed_gap():
    args = inputs()
    change_payload(args, "history", lambda p: p["data"].pop(1))
    out = describe_okx_funding_pair(**args)
    assert out["history"][-1]["preceding_observed_gap_hours"] == "16"
    assert out["history"][-1]["effective_interval_verified"] is False
    denied(out)


@pytest.mark.parametrize("field,value", [
    ("url", "https://www.okx.com/api/v5/public/funding-rate-history?instId=BTC-USDT-SWAP&limit=5"),
    ("url", "https://www.okx.com.evil/api/v5/public/funding-rate?instId=BTC-USDT-SWAP"),
    ("url", "https://www.okx.com/api/v5/public/funding-rate?instId=ETH-USDT-SWAP"),
    ("url", "https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP&instId=BTC-USDT-SWAP"),
    ("url", None),
    ("body_sha256", "bad"), ("body_bytes", True), ("curl_exit_code", True),
    ("http_status", "500"), ("received_at", "2026-10-29T00:00:00Z"),
    ("received_at", "2026-10-29T00:00:02"),
])
def test_receipt_or_endpoint_failure_refuses(field, value):
    args = inputs()
    args["current_receipt"][field] = value
    with pytest.raises(ValueError):
        describe_okx_funding_pair(**args)


@pytest.mark.parametrize("change", [
    lambda p: p.update(code="50000"),
    lambda p: p["data"][0].update(instId="ETH-USDT-SWAP"),
    lambda p: p["data"][0].update(instType="SPOT"),
    lambda p: p["data"].append(deepcopy(p["data"][0])),
    lambda p: p["data"][0].update(fundingTime=str(BASE + HOUR)),
    lambda p: p["data"][0].update(fundingTime=True),
])
def test_bad_history_is_not_silently_filtered(change):
    args = inputs()
    change_payload(args, "history", change)
    with pytest.raises(ValueError):
        describe_okx_funding_pair(**args)


def test_caller_flags_formula_tags_and_extra_intervals_never_qualify():
    args = inputs()
    change_payload(args, "current", lambda p: p["data"][0].update(
        eligible=True, interval_hours=8, formulaType="verified", normalization_eligible=True))
    out = describe_okx_funding_pair(**args)
    denied(out)
    out["raw_current"]["data"][0]["fundingRate"] = "changed"
    assert json.loads(args["current_body"])["data"][0]["fundingRate"] == "0.0002"


def test_duplicate_json_keys_are_refused():
    args = inputs()
    body = b'{"code":"0","code":"50000","data":[]}'
    args.update(current_body=body, current_receipt=receipt(body, "funding-rate"))
    with pytest.raises(ValueError, match="duplicate_json_key"):
        describe_okx_funding_pair(**args)


@pytest.mark.parametrize("constant", [b"NaN", b"Infinity", b"-Infinity"])
def test_nonfinite_json_is_refused(constant):
    args = inputs()
    body = b'{"code":"0","data":[],"extra":' + constant + b'}'
    args.update(current_body=body, current_receipt=receipt(body, "funding-rate"))
    with pytest.raises(ValueError, match="nonfinite_json"):
        describe_okx_funding_pair(**args)


def test_saved_reviewed_public_sample_is_a_contract_fixture_not_a_market_run():
    root = Path(__file__).resolve().parents[1]
    bindings = json.loads((root / "docs/review_artifacts/okx_funding_metadata_20261029/BINDINGS.json").read_bytes())
    capture = root / "docs/review_artifacts/okx_funding_metadata_20261029/20261029T103617Z_2668220f5a85484580a593b0207494d4"
    manifest = json.loads((capture / "MANIFEST.json").read_bytes())
    args = {"requested_inst_id": "BTC-USDT-SWAP"}
    for name in ("current", "history"):
        item = next(r for r in manifest["records"] if r["name"] == name)
        path = capture / item["body_file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == bindings[str(path.relative_to(root))]
        args[name + "_body"] = path.read_bytes()
        args[name + "_receipt"] = item
    out = describe_okx_funding_pair(**args)
    assert out["cross_checks"]["reported_settled_rate_matches_history"] is True
    assert out["cross_checks"]["current_rate_differs_from_reported_settlement"] is True
    assert [r["preceding_observed_gap_hours"] for r in out["history"]] == [None, "8", "8", "8", "8"]
    denied(out)
