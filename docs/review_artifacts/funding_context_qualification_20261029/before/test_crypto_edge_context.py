from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from services.strategies.crypto_edge_context import funding_context_from_crypto_edge_store
from storage.crypto_edge_store_sqlite import CryptoEdgeStoreSQLite


def test_funding_context_uses_latest_matching_live_public_row(tmp_path) -> None:
    store = CryptoEdgeStoreSQLite(path=str(tmp_path / "crypto_edges.sqlite"))
    store.append_funding_rows(
        [{"symbol": "BTC/USDT:USDT", "venue": "okx", "funding_rate": 0.0001}],
        source="live_public",
        capture_ts="2026-07-10T08:00:00+00:00",
        snapshot_id="funding-old",
    )
    store.append_funding_rows(
        [{"symbol": "BTC/USDT:USDT", "venue": "okx", "funding_rate": 0.0008, "interval_hours": 8}],
        source="live_public",
        capture_ts="2026-07-10T16:00:00+00:00",
        snapshot_id="funding-new",
    )
    store.append_funding_rows(
        [{"symbol": "BTC/USDT:USDT", "venue": "okx", "funding_rate": 0.0099}],
        source="sample_bundle",
        capture_ts="2026-07-10T17:00:00+00:00",
        snapshot_id="funding-sample",
    )

    result = funding_context_from_crypto_edge_store(
        symbol="BTC/USDT:USDT",
        venue="okx",
        source="live_public",
        max_age_sec=36 * 60 * 60,
        store=store,
        now=datetime(2026, 7, 10, 18, tzinfo=timezone.utc),
    )

    assert result["ok"] is True
    assert result["reason"] == "funding_context_ready"
    assert result["snapshot_id"] == "funding-new"
    funding = result["context"]["funding"]
    assert funding["funding_rate"] == 0.0008
    assert funding["funding_rate_pct"] == 0.08
    assert funding["source"] == "live_public"


def test_funding_context_fails_closed_when_missing_or_stale(tmp_path) -> None:
    store = CryptoEdgeStoreSQLite(path=str(tmp_path / "crypto_edges.sqlite"))
    store.append_funding_rows(
        [{"symbol": "BTC/USDT:USDT", "venue": "okx", "funding_rate": 0.0008}],
        source="live_public",
        capture_ts="2026-07-08T00:00:00+00:00",
        snapshot_id="funding-stale",
    )

    missing = funding_context_from_crypto_edge_store(
        symbol="ETH/USDT:USDT",
        venue="okx",
        source="live_public",
        store=store,
        now=datetime(2026, 7, 10, tzinfo=timezone.utc),
    )
    assert missing["ok"] is False
    assert missing["reason"] == "funding_context_missing"
    assert "context" not in missing

    stale = funding_context_from_crypto_edge_store(
        symbol="BTC/USDT:USDT",
        venue="okx",
        source="live_public",
        max_age_sec=60.0,
        store=store,
        now=datetime(2026, 7, 10, tzinfo=timezone.utc),
    )
    assert stale["ok"] is False
    assert stale["reason"] == "funding_context_stale"
    assert "context" not in stale


def test_funding_context_can_use_env_db_path(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "canonical" / "crypto_edge_research.sqlite"
    store = CryptoEdgeStoreSQLite(path=str(db_path))
    store.append_funding_rows(
        [{"symbol": "BTC/USDT:USDT", "venue": "okx", "funding_rate": 0.0007}],
        source="live_public",
        capture_ts="2026-07-10T08:00:00+00:00",
        snapshot_id="funding-env",
    )
    monkeypatch.setenv("CBP_CRYPTO_EDGE_DB_PATH", str(db_path))

    result = funding_context_from_crypto_edge_store(
        symbol="BTC/USDT:USDT",
        venue="okx",
        source="live_public",
        max_age_sec=36 * 60 * 60,
        now=datetime(2026, 7, 10, 9, tzinfo=timezone.utc),
    )

    assert result["ok"] is True
    assert result["snapshot_id"] == "funding-env"
    assert result["context"]["funding"]["funding_rate"] == 0.0007


def test_funding_context_env_db_missing_fails_closed_without_creating(monkeypatch, tmp_path: Path) -> None:
    missing = tmp_path / "missing" / "crypto_edge_research.sqlite"
    monkeypatch.setenv("CBP_CRYPTO_EDGE_DB_PATH", str(missing))

    result = funding_context_from_crypto_edge_store(
        symbol="BTC/USDT:USDT",
        venue="okx",
        source="live_public",
    )

    assert result["ok"] is False
    assert result["reason"] == "funding_context_store_missing"
    assert missing.exists() is False
