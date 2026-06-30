from __future__ import annotations

from services.analytics.short_context_readiness import build_short_context_readiness
from storage.crypto_edge_store_sqlite import CryptoEdgeStoreSQLite


def _write_required_rows(db_path, *, source: str, include_basis: bool = True) -> None:
    store = CryptoEdgeStoreSQLite(path=str(db_path))
    store.append_funding_rows(
        [{"symbol": "BTC/USDT:USDT", "venue": "binance", "funding_rate": 0.0001}],
        source=source,
        capture_ts="2026-03-18T10:00:00+00:00",
    )
    store.append_open_interest_rows(
        [{"symbol": "BTC/USDT:USDT", "venue": "binance", "open_interest": 12345.0}],
        source=source,
        capture_ts="2026-03-18T10:01:00+00:00",
    )
    if include_basis:
        store.append_basis_rows(
            [
                {
                    "symbol": "BTC/USDT:USDT",
                    "venue": "binance",
                    "spot_px": 84000.0,
                    "perp_px": 84050.0,
                    "days_to_expiry": 7,
                }
            ],
            source=source,
            capture_ts="2026-03-18T10:02:00+00:00",
        )
    store.append_order_book_rows(
        [
            {
                "symbol": "BTC/USD",
                "venue": "coinbase",
                "depth": 5,
                "best_bid": 84000.0,
                "best_ask": 84005.0,
                "spread_bps": 0.60,
                "bid_notional": 100000.0,
                "ask_notional": 95000.0,
                "imbalance": 0.0256,
            }
        ],
        source=source,
        capture_ts="2026-03-18T10:03:00+00:00",
    )


def test_short_context_readiness_missing_store_does_not_create_db(tmp_path) -> None:
    db_path = tmp_path / "missing.sqlite"

    out = build_short_context_readiness(db_path=db_path)

    assert out["ok"] is False
    assert out["status"] == "missing_store"
    assert out["live_public_replay_ready"] is False
    assert out["replay_scope"] == "fixture_only"
    assert not db_path.exists()


def test_short_context_readiness_fixture_source_stays_fixture_only(tmp_path) -> None:
    db_path = tmp_path / "crypto_edges.sqlite"
    _write_required_rows(db_path, source="sample_bundle")

    out = build_short_context_readiness(db_path=db_path, source="sample_bundle")

    assert out["ok"] is True
    assert out["status"] == "fixture_ready"
    assert out["fixture_replay_ready"] is True
    assert out["live_public_replay_ready"] is False
    assert out["replay_scope"] == "fixture_only"
    assert any("not live_public" in item for item in out["blockers"])


def test_short_context_readiness_blocks_partial_live_public_context(tmp_path) -> None:
    db_path = tmp_path / "crypto_edges.sqlite"
    _write_required_rows(db_path, source="live_public", include_basis=False)

    out = build_short_context_readiness(db_path=db_path, source="live_public")

    assert out["ok"] is True
    assert out["status"] == "live_public_partial"
    assert out["live_public_replay_ready"] is False
    assert out["missing_required_kinds"] == ["basis"]
    assert any("basis" in item for item in out["blockers"])


def test_short_context_readiness_accepts_complete_live_public_context(tmp_path) -> None:
    db_path = tmp_path / "crypto_edges.sqlite"
    _write_required_rows(db_path, source="live_public")

    out = build_short_context_readiness(db_path=db_path, source="live_public")

    assert out["ok"] is True
    assert out["status"] == "live_public_ready"
    assert out["live_public_replay_ready"] is True
    assert out["fixture_replay_ready"] is False
    assert out["replay_scope"] == "live_public"
    assert out["missing_required_kinds"] == []
