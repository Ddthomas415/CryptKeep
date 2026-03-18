from __future__ import annotations

from storage.crypto_edge_store_sqlite import CryptoEdgeStoreSQLite


def test_crypto_edge_store_persists_and_rebuilds_latest_report(tmp_path) -> None:
    store = CryptoEdgeStoreSQLite(path=str(tmp_path / "crypto_edges.sqlite"))

    funding_id = store.append_funding_rows(
        [{"symbol": "BTC-PERP", "venue": "binance", "funding_rate": 0.0001}],
        source="test",
        capture_ts="2026-03-18T10:00:00+00:00",
    )
    basis_id = store.append_basis_rows(
        [{"symbol": "BTC-PERP", "venue": "binance", "spot_px": 84000.0, "perp_px": 84050.0, "days_to_expiry": 30}],
        source="test",
        capture_ts="2026-03-18T10:00:00+00:00",
    )
    quote_id = store.append_quote_rows(
        [
            {"symbol": "BTC/USD", "venue": "coinbase", "bid": 84010.0, "ask": 84015.0},
            {"symbol": "BTC/USD", "venue": "kraken", "bid": 84020.0, "ask": 84005.0},
        ],
        source="test",
        capture_ts="2026-03-18T10:00:00+00:00",
    )

    report = store.latest_report()

    assert funding_id.startswith("funding-")
    assert basis_id.startswith("basis-")
    assert quote_id.startswith("quotes-")
    assert report["has_any_data"] is True
    assert report["funding"]["count"] == 1
    assert report["basis"]["count"] == 1
    assert report["dislocations"]["positive_count"] == 1
    assert report["dislocations"]["top_dislocation"]["symbol"] == "BTC/USD"
    assert report["funding_meta"]["source"] == "test"
    assert report["basis_meta"]["source"] == "test"
    assert report["quote_meta"]["source"] == "test"


def test_crypto_edge_store_exposes_recent_snapshot_history(tmp_path) -> None:
    store = CryptoEdgeStoreSQLite(path=str(tmp_path / "crypto_edges.sqlite"))
    store.append_funding_rows(
        [{"symbol": "BTC-PERP", "venue": "binance", "funding_rate": 0.0001}],
        source="hist",
        capture_ts="2026-03-18T10:00:00+00:00",
    )
    store.append_basis_rows(
        [{"symbol": "BTC-PERP", "venue": "binance", "spot_px": 84000.0, "perp_px": 84025.0, "days_to_expiry": 7}],
        source="hist",
        capture_ts="2026-03-18T10:05:00+00:00",
    )
    store.append_quote_rows(
        [{"symbol": "BTC/USD", "venue": "coinbase", "bid": 84010.0, "ask": 84005.0}],
        source="hist",
        capture_ts="2026-03-18T10:10:00+00:00",
    )

    rows = store.recent_snapshot_history(limit_per_kind=2)

    assert len(rows) == 3
    assert rows[0]["kind"] == "quotes"
    assert {row["kind"] for row in rows} == {"funding", "basis", "quotes"}


def test_crypto_edge_store_builds_per_kind_history_summaries(tmp_path) -> None:
    store = CryptoEdgeStoreSQLite(path=str(tmp_path / "crypto_edges.sqlite"))
    store.append_funding_rows(
        [{"symbol": "BTC-PERP", "venue": "binance", "funding_rate": 0.0001}],
        source="hist",
        capture_ts="2026-03-18T10:00:00+00:00",
    )
    store.append_funding_rows(
        [{"symbol": "BTC-PERP", "venue": "binance", "funding_rate": 0.0003}],
        source="hist",
        capture_ts="2026-03-18T11:00:00+00:00",
    )
    store.append_basis_rows(
        [{"symbol": "BTC-PERP", "venue": "binance", "spot_px": 84000.0, "perp_px": 84010.0, "days_to_expiry": 7}],
        source="hist",
        capture_ts="2026-03-18T10:05:00+00:00",
    )
    store.append_basis_rows(
        [{"symbol": "BTC-PERP", "venue": "binance", "spot_px": 84000.0, "perp_px": 84040.0, "days_to_expiry": 7}],
        source="hist",
        capture_ts="2026-03-18T11:05:00+00:00",
    )
    store.append_quote_rows(
        [
            {"symbol": "BTC/USD", "venue": "coinbase", "bid": 84010.0, "ask": 84015.0},
            {"symbol": "BTC/USD", "venue": "kraken", "bid": 84020.0, "ask": 84005.0},
        ],
        source="hist",
        capture_ts="2026-03-18T10:10:00+00:00",
    )
    store.append_quote_rows(
        [
            {"symbol": "BTC/USD", "venue": "coinbase", "bid": 84030.0, "ask": 84035.0},
            {"symbol": "BTC/USD", "venue": "kraken", "bid": 84050.0, "ask": 84000.0},
        ],
        source="hist",
        capture_ts="2026-03-18T11:10:00+00:00",
    )

    funding_history = store.recent_funding_history(limit=2)
    basis_history = store.recent_basis_history(limit=2)
    dislocation_history = store.recent_dislocation_history(limit=2)

    assert len(funding_history) == 2
    assert funding_history[0]["capture_ts"] == "2026-03-18T11:00:00+00:00"
    assert funding_history[0]["annualized_carry_pct"] > funding_history[1]["annualized_carry_pct"]
    assert funding_history[0]["dominant_bias"] == "long_pays"

    assert len(basis_history) == 2
    assert basis_history[0]["capture_ts"] == "2026-03-18T11:05:00+00:00"
    assert basis_history[0]["avg_basis_bps"] > basis_history[1]["avg_basis_bps"]

    assert len(dislocation_history) == 2
    assert dislocation_history[0]["capture_ts"] == "2026-03-18T11:10:00+00:00"
    assert dislocation_history[0]["positive_count"] >= 1
    assert dislocation_history[0]["top_gross_cross_bps"] >= dislocation_history[1]["top_gross_cross_bps"]


def test_crypto_edge_store_can_isolate_latest_report_for_live_public(tmp_path) -> None:
    store = CryptoEdgeStoreSQLite(path=str(tmp_path / "crypto_edges.sqlite"))
    store.append_funding_rows(
        [{"symbol": "BTC-PERP", "venue": "binance", "funding_rate": 0.0001}],
        source="sample_bundle",
        capture_ts="2026-03-18T09:00:00+00:00",
    )
    store.append_funding_rows(
        [{"symbol": "BTC-PERP", "venue": "binance", "funding_rate": 0.0002}],
        source="live_public",
        capture_ts="2026-03-18T10:00:00+00:00",
    )
    store.append_basis_rows(
        [{"symbol": "BTC-PERP", "venue": "binance", "spot_px": 84000.0, "perp_px": 84035.0, "days_to_expiry": 7}],
        source="live_public",
        capture_ts="2026-03-18T10:05:00+00:00",
    )

    report = store.latest_report_for_source(source="live_public")

    assert report["has_any_data"] is True
    assert report["funding"]["count"] == 1
    assert report["basis"]["count"] == 1
    assert report["dislocations"]["count"] == 0
    assert report["funding_meta"]["source"] == "live_public"
    assert report["basis_meta"]["source"] == "live_public"
    assert report["quote_meta"] is None
