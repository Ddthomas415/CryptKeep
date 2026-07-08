"""
Backlog #21 remaining-work proofs: OHLCV snapshot store carries source
provenance so sample-fed snapshots cannot launder into public ancestry.

The single snapshot writer records the actual source in a versioned
envelope; the legacy bare-list format still reads everywhere; a read-only
inspector exposes source/legacy for any consumer that needs to assert
public ancestry (fail-closed: legacy/corrupt reads report source unknown).
"""
from __future__ import annotations

import importlib
import json


def _reload_reader(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths
    import services.market_data.local_data_reader as reader

    importlib.reload(app_paths)
    importlib.reload(reader)
    return reader


ROWS = [
    [1, 100.0, 101.0, 99.0, 100.0, 1.0],
    [2, 100.0, 110.0, 100.0, 109.0, 1.0],
]


# ---------------------------------------------------------------------------
# writer envelope + reader compatibility
# ---------------------------------------------------------------------------


def test_writer_records_source_in_envelope_and_reader_still_returns_rows(monkeypatch, tmp_path):
    reader = _reload_reader(monkeypatch, tmp_path)
    path = reader.write_local_ohlcv_snapshot("coinbase", "BTC/USD", ROWS, timeframe="1d", source="sample_ohlcv")
    assert path is not None

    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["version"] == 2
    assert raw["source"] == "sample_ohlcv"
    assert raw["written_ts"]
    assert raw["candles"] == ROWS

    assert reader._load_local_ohlcv("coinbase", "BTC/USD", timeframe="1d", limit=10) == ROWS


def test_legacy_bare_list_snapshot_still_reads(monkeypatch, tmp_path):
    reader = _reload_reader(monkeypatch, tmp_path)
    path = reader._ohlcv_snapshot_path("coinbase", "ETH/USD", "1d")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ROWS), encoding="utf-8")

    assert reader._load_local_ohlcv("coinbase", "ETH/USD", timeframe="1d", limit=10) == ROWS

    prov = reader.load_local_ohlcv_snapshot_provenance("coinbase", "ETH/USD", timeframe="1d")
    assert prov["exists"] is True
    assert prov["legacy"] is True
    assert prov["source"] == "unknown"
    assert prov["row_count"] == 2


def test_writer_is_idempotent_for_same_rows_and_source(monkeypatch, tmp_path):
    reader = _reload_reader(monkeypatch, tmp_path)
    path = reader.write_local_ohlcv_snapshot("coinbase", "BTC/USD", ROWS, timeframe="1d", source="public_ohlcv")
    first = path.read_text(encoding="utf-8")
    reader.write_local_ohlcv_snapshot("coinbase", "BTC/USD", ROWS, timeframe="1d", source="public_ohlcv")
    assert path.read_text(encoding="utf-8") == first  # written_ts preserved, no churn


def test_writer_rewrites_when_source_changes(monkeypatch, tmp_path):
    reader = _reload_reader(monkeypatch, tmp_path)
    reader.write_local_ohlcv_snapshot("coinbase", "BTC/USD", ROWS, timeframe="1d", source="public_ohlcv")
    reader.write_local_ohlcv_snapshot("coinbase", "BTC/USD", ROWS, timeframe="1d", source="sample_ohlcv")
    prov = reader.load_local_ohlcv_snapshot_provenance("coinbase", "BTC/USD", timeframe="1d")
    assert prov["source"] == "sample_ohlcv"
    assert prov["legacy"] is False


def test_provenance_inspector_fail_closed_cases(monkeypatch, tmp_path):
    reader = _reload_reader(monkeypatch, tmp_path)

    missing = reader.load_local_ohlcv_snapshot_provenance("coinbase", "NO/PAIR", timeframe="1d")
    assert missing["exists"] is False
    assert missing["source"] == "unknown"

    path = reader._ohlcv_snapshot_path("coinbase", "BAD/PAIR", "1d")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not json", encoding="utf-8")
    corrupt = reader.load_local_ohlcv_snapshot_provenance("coinbase", "BAD/PAIR", timeframe="1d")
    assert corrupt["exists"] is True
    assert corrupt["source"] == "unknown"
    assert corrupt["legacy"] is True


def test_writer_default_source_is_unknown_not_public(monkeypatch, tmp_path):
    """A caller that forgets to pass source must not mint public ancestry."""
    reader = _reload_reader(monkeypatch, tmp_path)
    reader.write_local_ohlcv_snapshot("coinbase", "BTC/USD", ROWS, timeframe="1d")
    prov = reader.load_local_ohlcv_snapshot_provenance("coinbase", "BTC/USD", timeframe="1d")
    assert prov["source"] == "unknown"


# ---------------------------------------------------------------------------
# runner persists fetch-branch truth
# ---------------------------------------------------------------------------


def _reload_strategy_runner(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("CBP_STARTUP_CONFIRM_FLAT", "true")

    import services.os.app_paths as app_paths
    import services.admin.config_editor as config_editor
    import services.market_data.local_data_reader as reader
    import storage.intent_queue_sqlite as intent_queue_sqlite
    import storage.paper_trading_sqlite as paper_trading_sqlite
    import storage.strategy_state_sqlite as strategy_state_sqlite
    import services.execution.strategy_runner as runner

    importlib.reload(app_paths)
    importlib.reload(config_editor)
    importlib.reload(reader)
    importlib.reload(intent_queue_sqlite)
    importlib.reload(paper_trading_sqlite)
    importlib.reload(strategy_state_sqlite)
    importlib.reload(runner)
    return runner, reader


def test_sample_fetch_persists_snapshot_labeled_sample(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_USE_SAMPLE_OHLCV", "1")
    runner, reader = _reload_strategy_runner(monkeypatch, tmp_path)

    rows, source_info = runner._fetch_public_ohlcv(
        {
            "signal_source": "public_ohlcv_1d",
            "venue": "coinbase",
            "symbol": "BTC/USDT",
            "min_bars": 20,
            "max_bars": 50,
        }
    )
    assert rows
    assert source_info["source"] == "sample_ohlcv"

    prov = reader.load_local_ohlcv_snapshot_provenance("coinbase", "BTC/USDT", timeframe="1d")
    assert prov["exists"] is True
    assert prov["legacy"] is False
    assert prov["source"] == "sample_ohlcv"


def test_live_fetch_persists_snapshot_labeled_public(monkeypatch, tmp_path):
    monkeypatch.delenv("CBP_USE_SAMPLE_OHLCV", raising=False)
    runner, reader = _reload_strategy_runner(monkeypatch, tmp_path)

    class _FakeExchange:
        def fetch_ohlcv(self, symbol, timeframe="1d", limit=50):
            return ROWS

        def close(self):
            return None

    monkeypatch.setattr(runner, "make_exchange", lambda venue, creds, enable_rate_limit=True: _FakeExchange())

    rows, source_info = runner._fetch_public_ohlcv(
        {
            "signal_source": "public_ohlcv_1d",
            "venue": "coinbase",
            "symbol": "BTC/USDT",
            "min_bars": 2,
            "max_bars": 2,
        }
    )
    assert rows
    assert source_info["source"] == "public_ohlcv"

    prov = reader.load_local_ohlcv_snapshot_provenance("coinbase", "BTC/USDT", timeframe="1d")
    assert prov["source"] == "public_ohlcv"
    assert prov["legacy"] is False


# ---------------------------------------------------------------------------
# signal_quality surfaces snapshot ancestry
# ---------------------------------------------------------------------------


def test_signal_quality_local_snapshot_reports_sample_ancestry(monkeypatch, tmp_path):
    reader = _reload_reader(monkeypatch, tmp_path)
    import services.analytics.signal_quality as sq

    importlib.reload(sq)
    reader.write_local_ohlcv_snapshot("coinbase", "BTC/USD", ROWS, timeframe="1d", source="sample_ohlcv")

    rows, meta = sq.load_ohlcv_for_signal_quality(venue="coinbase", symbol="BTC/USD", timeframe="1d")
    assert rows == ROWS
    assert meta["type"] == "local_snapshot"
    assert meta["snapshot_source"] == "sample_ohlcv"
    assert meta["snapshot_source_legacy"] is False


def test_signal_quality_legacy_snapshot_reports_unknown_ancestry(monkeypatch, tmp_path):
    reader = _reload_reader(monkeypatch, tmp_path)
    import services.analytics.signal_quality as sq

    importlib.reload(sq)
    path = reader._ohlcv_snapshot_path("coinbase", "BTC/USD", "1d")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ROWS), encoding="utf-8")

    rows, meta = sq.load_ohlcv_for_signal_quality(venue="coinbase", symbol="BTC/USD", timeframe="1d")
    assert rows == ROWS
    assert meta["snapshot_source"] == "unknown"
    assert meta["snapshot_source_legacy"] is True


def test_signal_quality_explicit_file_reports_envelope_source(monkeypatch, tmp_path):
    import services.analytics.signal_quality as sq

    importlib.reload(sq)
    envelope = tmp_path / "ohlcv.json"
    envelope.write_text(
        json.dumps({"version": 2, "source": "sample_ohlcv", "written_ts": "x", "candles": ROWS}),
        encoding="utf-8",
    )
    rows, meta = sq.load_ohlcv_for_signal_quality(ohlcv_path=envelope)
    assert rows == ROWS
    assert meta["type"] == "explicit_file"
    assert meta["snapshot_source"] == "sample_ohlcv"
    assert meta["snapshot_source_legacy"] is False

    bare = tmp_path / "bare.json"
    bare.write_text(json.dumps(ROWS), encoding="utf-8")
    rows, meta = sq.load_ohlcv_for_signal_quality(ohlcv_path=bare)
    assert rows == ROWS
    assert meta["snapshot_source"] == "unknown"
    assert meta["snapshot_source_legacy"] is True
