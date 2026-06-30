from __future__ import annotations

import json

from scripts import check_short_context_readiness as script
from storage.crypto_edge_store_sqlite import CryptoEdgeStoreSQLite


def test_check_short_context_readiness_script_returns_zero_when_live_ready(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    db_path = tmp_path / "crypto_edges.sqlite"
    store = CryptoEdgeStoreSQLite(path=str(db_path))
    store.append_funding_rows(
        [{"symbol": "BTC/USDT:USDT", "venue": "binance", "funding_rate": 0.0001}],
        source="live_public",
        capture_ts="2026-03-18T10:00:00+00:00",
    )
    store.append_open_interest_rows(
        [{"symbol": "BTC/USDT:USDT", "venue": "binance", "open_interest": 12345.0}],
        source="live_public",
        capture_ts="2026-03-18T10:01:00+00:00",
    )
    store.append_basis_rows(
        [{"symbol": "BTC/USDT:USDT", "venue": "binance", "spot_px": 84000.0, "perp_px": 84050.0}],
        source="live_public",
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
        source="live_public",
        capture_ts="2026-03-18T10:03:00+00:00",
    )
    monkeypatch.setattr(
        script.sys,
        "argv",
        [
            "check_short_context_readiness.py",
            "--db-path",
            str(db_path),
            "--json",
        ],
    )

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "live_public_ready"
    assert out["live_public_replay_ready"] is True


def test_check_short_context_readiness_script_returns_one_when_blocked(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    db_path = tmp_path / "missing.sqlite"
    monkeypatch.setattr(
        script.sys,
        "argv",
        [
            "check_short_context_readiness.py",
            "--db-path",
            str(db_path),
            "--json",
        ],
    )

    assert script.main() == 1
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "missing_store"
    assert out["live_public_replay_ready"] is False
