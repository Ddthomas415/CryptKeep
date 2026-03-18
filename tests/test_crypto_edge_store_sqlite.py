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
