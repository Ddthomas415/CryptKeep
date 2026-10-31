"""Diagnostic reproductions of current Fix3 gaps, not repaired behavior."""
from __future__ import annotations

import ast
from collections import defaultdict
import json
from pathlib import Path
import socket
import sqlite3
import sys
import time
from types import SimpleNamespace

import pytest

from services.markets.math_utils import decimal_value


ROOT = Path(__file__).resolve().parents[1]


def selected(path, names, namespace):
    tree = ast.parse((ROOT / path).read_bytes())
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes} == set(names)
    module = ast.Module(body=nodes, type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), path, "exec"), namespace)
    return namespace


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("network forbidden in diagnostic")
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)


def collect(payload, plan_interval=None):
    trace = []
    exchange = SimpleNamespace(fetch_funding_rate=lambda symbol: dict(payload))
    ns = selected("services/analytics/crypto_edge_collector.py",
                  {"_extract_funding_rate", "_collect_funding_rows"},
                  {"defaultdict": defaultdict, "normalize_venue": str,
                   "map_symbol": lambda venue, symbol: symbol,
                   "_open_public_exchange": lambda venue: exchange,
                   "_close_exchange": lambda ex: trace.append("close")})
    plan = {"venue": "okx", "symbol": "EXAMPLE/USDT:USDT"}
    if plan_interval is not None:
        plan["interval_hours"] = plan_interval
    rows, checks = ns["_collect_funding_rows"]([plan])
    assert trace == ["close"]
    return rows, checks


def test_unknown_interval_is_currently_reported_as_eight_hours():
    rows, checks = collect({"fundingRate": 0.0001})
    assert rows[0]["interval_hours"] == 8.0
    assert checks[0]["ok"] is True


@pytest.mark.parametrize("interval", ["1h", "4h"])
def test_payload_interval_currently_loses_to_plan(interval):
    rows, _ = collect({"fundingRate": 0.0001, "interval": interval}, 8.0)
    assert rows[0]["interval_hours"] == 8.0


def test_predicted_rate_is_currently_indistinguishable_after_collection():
    predicted, _ = collect({"nextFundingRate": 0.0001})
    current, _ = collect({"fundingRate": 0.0001})
    assert predicted == current
    assert "rate_source_field" not in predicted[0]


def test_exchange_times_and_formula_provenance_are_currently_discarded():
    rows, _ = collect({"fundingRate": 0.0001, "timestamp": 1700000000000,
                       "fundingTimestamp": 1700003600000,
                       "info": {"fundingTime": "1700003600000",
                                "nextFundingRate": "0.0002"}})
    assert set(rows[0]) == {"symbol", "venue", "funding_rate", "interval_hours"}


def test_store_currently_drops_extra_provenance_even_if_caller_supplies_it():
    path = "storage/crypto_edge_store_sqlite.py"
    tree = ast.parse((ROOT / path).read_bytes())
    ddl = next(n.value.value for n in tree.body if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == "DDL" for t in n.targets))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "CryptoEdgeStoreSQLite")
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "append_funding_rows")
    ns = selected(path, {"_s", "_required_float", "_optional_float"},
                  {"decimal_value": decimal_value, "math": __import__("math"), "json": json})
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])), path, "exec"), ns)
    with sqlite3.connect(":memory:") as conn:
        conn.executescript(ddl)
        store = SimpleNamespace(_connect=lambda: conn)
        row = {"symbol": "EXAMPLE", "venue": "okx", "funding_rate": 0.0001,
               "interval_hours": 4.0, "rate_source_field": "nextFundingRate",
               "rate_kind": "predicted", "exchange_timestamp": 1700000000000,
               "next_settlement_timestamp": 1700003600000, "formula_version": "unknown"}
        ns["append_funding_rows"](store, [row], capture_ts="2026-10-28T00:00:00Z",
                                  snapshot_id="invented", source="synthetic")
        saved = json.loads(conn.execute("SELECT payload_json FROM funding_snapshots").fetchone()[0])
        assert set(saved) == {"symbol", "venue", "funding_rate", "interval_hours"}
    conn.close()


def funding_summary(monkeypatch, rate, interval):
    fake = SimpleNamespace(fetch_funding_rate=lambda symbol: {"fundingRate": rate, "interval": interval},
                           close=lambda: None)
    monkeypatch.setitem(sys.modules, "ccxt", SimpleNamespace(binance=lambda config: fake))
    ns = selected("services/market_data/alternative_data.py", {"get_funding_rates"}, {"time": time})
    result = ns["get_funding_rates"](["EXAMPLE/USDT"])
    assert result["ok"] is True and len(result["rates"]) == 1
    return result["rates"][0]


def test_equal_synthetic_per_hour_rates_currently_get_different_crowding_flags(monkeypatch):
    hourly = funding_summary(monkeypatch, 0.0001, "1h")
    eight_hourly = funding_summary(monkeypatch, 0.0008, "8h")
    assert hourly["signal"] == "neutral"
    assert eight_hourly["signal"] == "overleveraged_longs"
    assert hourly["annualized"] == pytest.approx(10.95)
    assert eight_hourly["annualized"] == pytest.approx(87.6)
    # Equivalent constant-rate toy schedules, not a venue formula or yield forecast.
    assert 0.0001 * 24 * 365 == pytest.approx(0.0008 * 3 * 365)


def test_archive_summary_currently_ignores_per_row_interval():
    ns = selected("services/analytics/crypto_edges.py",
                  {"_fnum", "_s", "summarize_funding_carry"}, {})
    summary = ns["summarize_funding_carry"]
    hourly = summary([{"funding_rate": 0.0001, "interval_hours": 1.0}])
    eight_hourly = summary([{"funding_rate": 0.0008, "interval_hours": 8.0}])
    assert hourly["annualized_carry_pct"] == pytest.approx(10.95)
    assert eight_hourly["annualized_carry_pct"] == pytest.approx(87.6)
