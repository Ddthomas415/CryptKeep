from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path
import socket
import sqlite3

import pytest

from scripts.research.synthetic_okx_cash_cost import compare_okx_cash_costs


BASE = int(datetime(2026, 10, 29, tzinfo=timezone.utc).timestamp() * 1000)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("network/database boundary forbidden")
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(sqlite3, "connect", refuse)


def inputs(hours=8, rate="0.0001", **changes):
    current = {"instId": "BTC-USDT-SWAP", "instType": "SWAP", "fundingRate": rate,
               "settFundingRate": "0.0002", "settState": "settled", "method": "current_period",
               "ts": str(BASE + 1000), "fundingTime": str(BASE + 3600000),
               "nextFundingTime": str(BASE + 3600000 + int(hours * 3600000)),
               "prevFundingTime": str(BASE)}
    current.update(changes)
    history = [{"instId": "BTC-USDT-SWAP", "instType": "SWAP", "realizedRate": "0.0002",
                "fundingRate": "0.9", "fundingTime": str(BASE - n * 3600000 * 8)} for n in range(2)]
    result = {"requested_inst_id": "BTC-USDT-SWAP"}
    for name, data in (("current", [current]), ("history", history)):
        body = json.dumps({"code": "0", "data": data}).encode()
        endpoint = "funding-rate" + ("-history" if name == "history" else "")
        result[name + "_body"] = body
        result[name + "_receipt"] = {
            "url": "https://www.okx.com/api/v5/public/" + endpoint + "?instId=BTC-USDT-SWAP"
            + ("&limit=5" if name == "history" else ""),
            "curl_exit_code": 0, "http_status": "200", "body_bytes": len(body),
            "body_sha256": hashlib.sha256(body).hexdigest(),
            "request_started_at": "2026-10-29T00:00:01Z", "received_at": "2026-10-29T00:00:02Z"}
    return result


def no_authority(out):
    assert out["strategy_eligible"] is False and out["execution_authority"] is False
    assert out["crowding_comparable"] is False and out["formula_inversion_performed"] is False
    assert out["annualized_pct"] is None
    assert out["evidence"]["normalization_eligible"] is False
    assert out["forecast_cash_cost"]["live_freshness_verified"] is False
    assert all(row["settled_rate_per_8h"] is None for row in out["reported_settlements"])


@pytest.mark.parametrize("hours", [1, 2, 4, 6, 8, 16])
def test_equivalent_synthetic_period_costs_have_same_eight_hour_forecast(hours):
    rate = str(Decimal("0.00001") * hours)
    out = compare_okx_cash_costs(**inputs(hours, rate))
    quote = out["forecast_cash_cost"]
    assert quote["calculation_available"] is True
    assert Decimal(quote["forecast_rate_per_8h"]) == Decimal("0.00008")
    assert quote["scheduled_interval_hours"] == str(hours)
    assert quote["kind"] == "forecast_not_settled"
    no_authority(out)


@pytest.mark.parametrize("rate", ["0", "-0.0002", "0.0002"])
@pytest.mark.parametrize("formula", [None, "noRate", "withRate", "unknown"])
def test_sign_zero_and_cash_arithmetic_do_not_require_premium_formula(rate, formula):
    out = compare_okx_cash_costs(**inputs(8, rate, formulaType=formula))
    assert Decimal(out["forecast_cash_cost"]["forecast_rate_per_8h"]) == Decimal(rate)
    assert out["forecast_cash_cost"]["positive_rate_means"] == "long_pays_short"
    assert out["reported_settlements"][-1]["per_period_decimal_rate"] == "0.0002"
    no_authority(out)


@pytest.mark.parametrize("changes,reason", [
    ({"method": None}, "current_period_mechanism_required"),
    ({"method": "next_period"}, "current_period_mechanism_required"),
    ({"ts": None}, "source_time_unknown_or_future"),
    ({"ts": str(BASE + 3000)}, "source_time_unknown_or_future"),
    ({"fundingTime": str(BASE)}, "settlement_not_upcoming_at_receipt"),
    ({"nextFundingTime": None}, "scheduled_interval_unknown"),
    ({"nextFundingTime": str(BASE + 3600000)}, "scheduled_interval_unknown"),
])
def test_uncertain_basis_produces_no_forecast_normalization(changes, reason):
    out = compare_okx_cash_costs(**inputs(**changes))
    quote = out["forecast_cash_cost"]
    assert quote["calculation_available"] is False
    assert quote["forecast_rate_per_8h"] is None and reason in quote["reasons"]
    no_authority(out)


@pytest.mark.parametrize("rate", [None, "", "NaN", "Infinity", "bad", True])
def test_bad_rate_is_unknown_not_zero(rate):
    quote = compare_okx_cash_costs(**inputs(rate=rate))["forecast_cash_cost"]
    assert quote["forecast_rate_per_8h"] is None
    assert "forecast_rate_unknown" in quote["reasons"]


@pytest.mark.parametrize("rate", ["1e9999999", "1e-9999999"])
def test_unrepresentable_arithmetic_refuses_without_defaulting(rate):
    out = compare_okx_cash_costs(**inputs(rate=rate))
    assert out["forecast_cash_cost"]["calculation_available"] is False
    assert out["forecast_cash_cost"]["forecast_rate_per_8h"] is None
    assert "cash_cost_arithmetic_unrepresentable" in out["forecast_cash_cost"]["reasons"]
    no_authority(out)


def test_precision_context_and_output_mutations_do_not_change_input_contract():
    args = inputs(1, "0.0000123456789")
    original = deepcopy(args)
    with localcontext() as ctx:
        ctx.prec = 2
        out = compare_okx_cash_costs(**args)
    assert Decimal(out["forecast_cash_cost"]["forecast_rate_per_8h"]) == Decimal("0.0000987654312")
    out["evidence"]["raw_current"]["data"][0]["fundingRate"] = "mutated"
    assert args == original


def test_forged_receipt_is_refused_before_any_cash_calculation():
    args = inputs()
    args["current_receipt"]["body_sha256"] = "bad"
    with pytest.raises(ValueError, match="receipt_integrity_failed"):
        compare_okx_cash_costs(**args)


def test_reviewed_saved_sample_uses_forecast_interval_not_historical_gap():
    root = Path(__file__).resolve().parents[1]
    path = root / "docs/review_artifacts/okx_funding_metadata_20261029/20261029T103617Z_2668220f5a85484580a593b0207494d4"
    manifest = json.loads((path / "MANIFEST.json").read_bytes())
    args = {"requested_inst_id": "BTC-USDT-SWAP"}
    for name in ("current", "history"):
        record = next(row for row in manifest["records"] if row["name"] == name)
        args[name + "_body"] = (path / record["body_file"]).read_bytes()
        args[name + "_receipt"] = record
    out = compare_okx_cash_costs(**args)
    quote = out["forecast_cash_cost"]
    assert quote["calculation_available"] is True
    assert quote["scheduled_interval_hours"] == "8"
    assert Decimal(quote["forecast_rate_per_8h"]) == Decimal("0.0000436849743302")
    assert out["reported_settlements"][-1]["per_period_decimal_rate"] == "0.0000338041564747"
    no_authority(out)
