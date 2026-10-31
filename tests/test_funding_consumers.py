from __future__ import annotations

import ast
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from itertools import count
import json
from pathlib import Path
import socket
import sys
from types import SimpleNamespace

import pytest

from services.market_data import alternative_data as alternative
from services.market_data import composite_ranker as ranker


ROOT = Path(__file__).resolve().parents[1]
BEFORE = ROOT / "docs/review_artifacts/funding_consumers_20261029/before"


@pytest.fixture
def sdk(monkeypatch):
    trace = []
    payloads = {"EXAMPLE/USDT": {"fundingRate": 0.0001}}
    errors = {}
    class Fake:
        def fetch_funding_rate(self, symbol):
            trace.append(("fetch", symbol))
            if symbol in errors:
                raise errors[symbol]
            return deepcopy(payloads[symbol])
        def close(self):
            trace.append("close")
            if "close" in errors:
                raise errors["close"]
    def build(config):
        trace.append(("build", config))
        return Fake()
    monkeypatch.setitem(sys.modules, "ccxt", SimpleNamespace(binance=build))
    ticks = count()
    base = datetime(2026, 10, 29, tzinfo=timezone.utc)
    monkeypatch.setattr(alternative, "_funding_utc_now",
                        lambda: (base + timedelta(seconds=next(ticks))).isoformat(), raising=False)
    def refuse(*args, **kwargs):
        raise AssertionError("network forbidden")
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(alternative, "_get_json", refuse)
    return payloads, errors, trace


def test_unknown_interval_never_becomes_annualized_income_or_neutral(sdk):
    result = alternative.get_funding_rates(["EXAMPLE/USDT"])
    row = result["rates"][0]
    assert row["annualized"] is None
    assert row["signal"] == "unknown"
    assert row["rate_pct"] is None
    assert row["raw_rate_pct"] == pytest.approx(0.01)
    assert row["normalization_eligible"] is False


@pytest.mark.parametrize("interval", [None, "1h", "4h", "8h"])
@pytest.mark.parametrize("rate", [0, 0.0001, -0.0001])
def test_interval_and_rate_sign_alone_never_certify_crowding_or_yield(sdk, interval, rate):
    payloads, _, trace = sdk
    payloads["EXAMPLE/USDT"] = {"fundingRate": rate, "interval": interval}
    row = alternative.get_funding_rates(["EXAMPLE/USDT"])["rates"][0]
    assert row["raw_rate_pct"] == pytest.approx(rate * 100)
    assert row["signal"] == "unknown" and row["annualized"] is None and row["rate_pct"] is None
    assert row["observation"]["interval_hours"] == (int(interval[:-1]) if interval else None)
    assert trace[-1] == "close"
    assert [x for x in trace if isinstance(x, tuple) and x[0] == "fetch"] == [("fetch", "EXAMPLE/USDT")]


def test_payload_native_fields_and_receipt_survive_without_settled_claim(sdk):
    payloads, _, _ = sdk
    raw = {"nextFundingRate": "0.0001", "symbol": "OTHER",
           "info": {"nextFundingRate": "0.0001", "time": 1700000000000,
                    "fundingTime": "1700003600000"}}
    payloads["EXAMPLE/USDT"] = deepcopy(raw)
    row = alternative.get_funding_rates(["EXAMPLE/USDT"])["rates"][0]
    record = row["observation"]
    assert record["raw_payload"] == raw and record["rate_kind"] == "predicted"
    assert record["rate_kind_verified"] is False
    assert record["receipt"]["response_symbol_matches_request"] is False
    assert record["receipt"]["request_started_at"] == "2026-10-29T00:00:00+00:00"
    assert record["captured_at"] == "2026-10-29T00:00:01+00:00"
    assert record["reported_exchange_time_fields"]["info.time"] == 1700000000000


@pytest.mark.parametrize("raw", [{}, {"fundingRate": None}, {"fundingRate": "nan"}, {"fundingRate": True}])
def test_unknown_rate_is_retained_not_zero_filled(sdk, raw):
    payloads, _, _ = sdk
    payloads["EXAMPLE/USDT"] = raw
    result = alternative.get_funding_rates(["EXAMPLE/USDT"])
    assert result["ok"] is True and result["complete"] is True
    assert result["normalization_eligible"] is False
    row = result["rates"][0]
    assert row["observation"]["raw_payload"] == raw
    assert row["raw_rate_pct"] is None and row["normalization_reason"] == "rate_unknown"


def test_partial_failure_is_visible_sanitized_and_closes(sdk):
    _, errors, trace = sdk
    errors["BAD/USDT"] = RuntimeError("sensitive-looking detail")
    result = alternative.get_funding_rates(["EXAMPLE/USDT", "BAD/USDT"])
    assert result["ok"] is True and result["complete"] is False
    assert len(result["rates"]) == 1 and len(result["errors"]) == 1
    assert result["errors"][0]["reason"] == "funding_observation_failed:RuntimeError"
    assert "sensitive-looking" not in json.dumps(result)
    assert trace[-1] == "close"


def test_close_failure_does_not_erase_observation_or_claim_complete(sdk):
    _, errors, _ = sdk
    errors["close"] = RuntimeError("sensitive-looking close detail")
    result = alternative.get_funding_rates(["EXAMPLE/USDT"])
    assert len(result["rates"]) == 1 and result["complete"] is False
    assert result["errors"] == [{"reason": "funding_close_failed:RuntimeError"}]


def test_all_fetches_fail_is_not_success(sdk):
    _, errors, trace = sdk
    errors["EXAMPLE/USDT"] = TimeoutError("invented")
    result = alternative.get_funding_rates(["EXAMPLE/USDT"])
    assert result["ok"] is False and result["complete"] is False
    assert result["rates"] == [] and result["reason"] == "funding_unavailable"
    assert trace[-1] == "close"


def test_overflowing_percent_conversion_does_not_leak_nonfinite_output(sdk):
    payloads, _, _ = sdk
    payloads["EXAMPLE/USDT"] = {"fundingRate": 1e308}
    result = alternative.get_funding_rates(["EXAMPLE/USDT"])
    row = result["rates"][0]
    assert row["raw_rate_pct"] is None and row["raw_percent_unrepresentable"] is True
    assert row["observation"]["raw_payload"]["fundingRate"] == 1e308
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("extra", [
    {"normalization_eligible": False}, {"normalization_eligible": True},
    {"normalization": {"eligible": True}}, {"observation": {"normalization": {"eligible": True}}},
])
def test_declarations_do_not_qualify_an_observation_for_ranker(extra):
    status = ranker.funding_input({"rate_pct": -0.08, **extra})
    assert status["rate_pct"] is None and status["state"] == "unverified"
    scored = ranker.score_row(row={"symbol": "EXAMPLE"}, funding_row={"rate_pct": -0.08, **extra})
    assert scored["score_breakdown"]["funding"] is None
    assert scored["funding_rate_pct"] is None


def archived_score():
    path = BEFORE / "composite_ranker.py"
    tree = ast.parse(path.read_bytes())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "score_row")
    ns = dict(vars(ranker))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(path), "exec"), ns)
    return ns["score_row"]


@pytest.mark.parametrize("rate", [-0.08, -0.01, -0.001, 0, 0.01, 0.02, 0.05, 0.08])
def test_frozen_numeric_legacy_model_score_and_thresholds_remain_unchanged(rate):
    row = {"symbol": "EXAMPLE", "change_pct": 3, "rsi": 60, "hot_score": 5,
           "volume_z": 1, "volatility_pct": 4}
    args = {"row": row, "funding_row": {"rate_pct": rate}}
    old, current = archived_score()(**args), ranker.score_row(**args)
    assert all(current[key] == value for key, value in old.items())
    assert current["funding_input_state"] == "legacy_unverified"


def test_unverified_funding_does_not_change_other_score_components(sdk):
    fresh = alternative.get_funding_rates(["EXAMPLE/USDT"])["rates"][0]
    row = {"symbol": "EXAMPLE", "change_pct": 3, "rsi": 60, "hot_score": 5,
           "volume_z": 1, "volatility_pct": 4}
    old = archived_score()(row=row, funding_row=None)
    current = ranker.score_row(row=row, funding_row=fresh)
    assert current["composite_score"] == old["composite_score"]
    assert all(value == current["score_breakdown"][key]
               for key, value in old["score_breakdown"].items() if key != "funding")
    assert current["score_breakdown"]["funding"] is None


@pytest.mark.parametrize("value", [None, True, "nan", "inf", "invalid"])
def test_invalid_legacy_rate_does_not_become_zero_or_threshold_signal(value):
    assert ranker.funding_input({"rate_pct": value})["rate_pct"] is None


def dashboard_signals(rows, path=ROOT / "dashboard/pages/40_Market_Intelligence.py"):
    tree = ast.parse(path.read_bytes())
    node = next(n for n in tree.body if isinstance(n, ast.For) and isinstance(n.iter, ast.Name)
                and n.iter.id == "funding_rows")
    def refuse(**kwargs):
        raise AssertionError("unverified data must not reach the strategy")
    ns = {"funding_rows": rows, "funding_signals": [], "funding_input": ranker.funding_input,
          "funding_signal_from_context": refuse}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(path), "exec"), ns)
    return ns["funding_signals"]


@pytest.mark.parametrize("row", [
    {"symbol": "EXAMPLE", "rate_pct": None, "normalization_eligible": False},
    {"symbol": "EXAMPLE", "rate_pct": 0.08},
    {"symbol": "EXAMPLE", "raw_rate_pct": -0.08, "normalization_eligible": False},
    {"symbol": "EXAMPLE"},
])
def test_dashboard_does_not_turn_unknown_or_legacy_unverified_into_actions(row):
    result = dashboard_signals([row])[0]
    assert result["action"] is None and result["funding_rate_pct"] is None
    assert result["reason"] != "funding_neutral"
    assert result["validation_state"] != "qualified"


def test_archived_dashboard_loop_is_a_negative_control():
    with pytest.raises(AssertionError, match="must not reach"):
        dashboard_signals([{"symbol": "EXAMPLE", "rate_pct": None}],
                          path=BEFORE / "40_Market_Intelligence.py")
