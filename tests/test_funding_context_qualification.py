from __future__ import annotations

import ast
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import socket
import sqlite3
from urllib.parse import unquote, urlsplit

import pytest

from services.strategies.crypto_edge_context import funding_context_from_crypto_edge_store
from services.strategies import crypto_edge_context as context
from services.analytics import funding_context_replay as replay
from services.analytics import funding_context_price_join as joined
from services.analytics.funding_observations import legacy_model_qualification
from services.strategies.strategy_registry import compute_signal
from storage.crypto_edge_store_sqlite import CryptoEdgeStoreSQLite
from storage.market_store_sqlite import MarketStore


ROOT = Path(__file__).resolve().parents[1]
BEFORE = ROOT / "docs/review_artifacts/funding_context_qualification_20261029/before"


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    trace = []
    connect = sqlite3.connect
    def temporary(database, *args, **kwargs):
        raw = str(database)
        if raw.startswith("file:"):
            parsed = urlsplit(raw)
            assert kwargs.get("uri") is True and parsed.query == "mode=ro"
            path = Path(unquote(parsed.path))
            trace.append(raw)
        else:
            path = Path(raw)
        assert path.resolve().is_relative_to(tmp_path.resolve())
        return connect(database, *args, **kwargs)
    def refuse(*args, **kwargs):
        raise AssertionError("external/initializing boundary forbidden")
    monkeypatch.setattr(sqlite3, "connect", temporary)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(context, "CryptoEdgeStoreSQLite", refuse)
    monkeypatch.delenv(context.EDGE_STORE_DB_PATH_ENV, raising=False)
    monkeypatch.setattr(context, "DEFAULT_EDGE_STORE_DB_PATH", tmp_path / "default-missing" / "edge.sqlite")
    return trace


class LegacyStore:
    def recent_funding_rows_for_source(self, **kwargs):
        return [{"capture_ts": "2026-10-29T00:00:00Z", "funding_rate": 0.0008,
                 "interval_hours": 8, "symbol": "EXAMPLE/USDT:USDT", "venue": "okx",
                 "source": "live_public", "snapshot_id": "invented"}]


def test_fresh_legacy_rate_is_not_a_qualified_strategy_context():
    result = funding_context_from_crypto_edge_store(
        symbol="EXAMPLE/USDT:USDT", venue="okx", store=LegacyStore(),
        now=datetime(2026, 10, 29, 1, tzinfo=timezone.utc))
    assert result["ok"] is False
    assert result["reason"] == "funding_context_unqualified"
    assert "context" not in result


@pytest.mark.parametrize("interval", [None, 1, 4, 8, 0, "bad"])
@pytest.mark.parametrize("claimed", [False, True])
def test_interval_or_boolean_does_not_qualify_a_legacy_context(interval, claimed):
    class Store(LegacyStore):
        def recent_funding_rows_for_source(self, **kwargs):
            row = super().recent_funding_rows_for_source(**kwargs)[0]
            row.update(interval_hours=interval, normalization_eligible=claimed)
            return [row]
    result = funding_context_from_crypto_edge_store(
        symbol="EXAMPLE/USDT:USDT", venue="okx", store=Store(),
        now=datetime(2026, 10, 29, 1, tzinfo=timezone.utc))
    assert result["ok"] is False and result["reason"] == "funding_context_unqualified"
    assert result["normalization_eligible"] is False and "context" not in result
    assert result["raw_observation"]["interval_hours"] == interval


def test_readonly_path_never_initializes_schema_and_escapes_uri(tmp_path, offline):
    path = tmp_path / "archive #? space.sqlite"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE funding_snapshots("
                     "id INTEGER PRIMARY KEY, snapshot_id TEXT,capture_ts TEXT,source TEXT,"
                     "symbol TEXT,venue TEXT,funding_rate REAL,interval_hours REAL,payload_json TEXT)")
        conn.execute("INSERT INTO funding_snapshots VALUES(1,'invented','2026-10-29T00:00:00Z',"
                     "'live_public','EXAMPLE/USDT:USDT','okx',0.0008,8,'{}')")
    before = path.read_bytes()
    result = funding_context_from_crypto_edge_store(
        symbol="EXAMPLE/USDT:USDT", venue="okx", store_path=path,
        now=datetime(2026, 10, 29, 1, tzinfo=timezone.utc))
    assert result["reason"] == "funding_context_unqualified" and "context" not in result
    assert path.read_bytes() == before
    assert len(offline) == 1 and "%23%3F" in offline[0]
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() == [("funding_snapshots",)]


def test_missing_default_does_not_create_database_or_parent(tmp_path):
    result = funding_context_from_crypto_edge_store(symbol="EXAMPLE", venue="okx")
    assert result["reason"] == "funding_context_store_missing"
    assert not (tmp_path / "default-missing").exists()


def test_store_error_is_sanitized():
    class Store:
        def recent_funding_rows_for_source(self, **kwargs):
            raise RuntimeError("sensitive-looking fake detail")
    result = funding_context_from_crypto_edge_store(symbol="EXAMPLE", venue="okx", store=Store())
    assert result["reason"] == "funding_context_store_error"
    assert result["error_type"] == "RuntimeError"
    assert "sensitive-looking" not in str(result)


def test_registry_runner_receives_no_unqualified_context():
    path = ROOT / "services/execution/strategy_runner.py"
    tree = ast.parse(path.read_bytes())
    names = {"_context_meta_from_result", "_registry_signal_with_context"}
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    ns = {"DEFAULT_CONTEXT_SOURCE": "live_public", "DEFAULT_FUNDING_MAX_AGE_SEC": 129600,
          "capture_es_inputs": lambda **kwargs: {}, "compute_signal": compute_signal,
          "funding_context_from_crypto_edge_store": lambda **kwargs: funding_context_from_crypto_edge_store(
              symbol=kwargs["symbol"], venue=kwargs["venue"], store=LegacyStore(),
              now=datetime(2026, 10, 29, 1, tzinfo=timezone.utc))}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(path), "exec"), ns)
    result = ns["_registry_signal_with_context"](
        cfg={}, strategy_block={"name": "funding_extreme"}, symbol="EXAMPLE/USDT:USDT", venue="okx", ohlcv=[])
    assert result["ok"] is False and result["action"] == "hold"
    assert result["reason"] == "missing_funding_context"
    assert result["strategy_context_reason"] == "funding_context_unqualified"


def old_function(module, filename, name):
    path = BEFORE / filename
    tree = ast.parse(path.read_bytes())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    ns = dict(vars(module))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(path), "exec"), ns)
    return ns[name]


def seed_edge(path):
    store = CryptoEdgeStoreSQLite(path=str(path))
    for timestamp, rate in (("2023-11-14T22:13:20Z", -0.0002), ("2023-11-14T22:23:20Z", 0.0008)):
        store.append_funding_rows(
            [{"symbol": "BTC/USDT:USDT", "venue": "okx", "funding_rate": rate, "interval_hours": 8}],
            source="live_public", capture_ts=timestamp)


def assert_model_equal(old, current):
    assert {k: v for k, v in current.items() if k not in {"funding_qualification", "generated_at"}} == {
        k: v for k, v in old.items() if k != "generated_at"}
    qualification = current["funding_qualification"]
    assert qualification["model_only"] is True
    assert qualification["normalization_eligible"] is False
    assert qualification["execution_authority"] is False
    assert qualification["cash_cost_basis_verified"] is False
    assert qualification["crowding_comparability_verified"] is False


def test_replay_qualification_does_not_change_model_actions_or_dataset_hash(tmp_path):
    path = tmp_path / "edge.sqlite"
    seed_edge(path)
    original = old_function(replay, "funding_context_replay.py", "run_funding_context_replay")
    args = {"db_path": path}
    assert_model_equal(original(**args), replay.run_funding_context_replay(**args))


def test_join_qualification_does_not_change_synthetic_returns_or_hashes(tmp_path):
    edge_path, archive_path = tmp_path / "edge.sqlite", tmp_path / "market.sqlite"
    seed_edge(edge_path)
    market = MarketStore(archive_path)
    for index, price in enumerate([100, 110, 100, 90, 91]):
        market.upsert_ohlcv(ts_ms=1700000000000 + index * 300000, exchange="okx", symbol="BTC/USDT",
                           timeframe="5m", o=price, h=price + 1, l=price - 1, cl=price, v=10)
    original = old_function(joined, "funding_context_price_join.py", "run_funding_context_price_join")
    args = {"edge_db_path": edge_path, "archive_db_path": archive_path,
            "ohlcv_limit": 5, "min_joined_rows": 2, "fee_bps": 0, "slippage_bps": 0}
    assert_model_equal(original(**args), joined.run_funding_context_price_join(**args))


def test_qualification_metadata_cannot_be_mutated_between_calls():
    first = legacy_model_qualification()
    first["normalization_eligible"] = True
    assert legacy_model_qualification()["normalization_eligible"] is False
