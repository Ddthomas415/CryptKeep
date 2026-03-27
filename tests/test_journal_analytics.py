from __future__ import annotations

from services.analytics.journal_analytics import fifo_pnl_from_fills


def test_fifo_pnl_from_fills_allocates_trade_fees() -> None:
    fills = [
        {"fill_ts": "2026-03-19T12:00:00Z", "symbol": "BTC/USD", "side": "buy", "qty": 1.0, "price": 100.0, "fee": 1.0},
        {"fill_ts": "2026-03-19T12:10:00Z", "symbol": "BTC/USD", "side": "sell", "qty": 1.0, "price": 110.0, "fee": 2.0},
    ]

    out = fifo_pnl_from_fills(fills)

    assert out["summary"]["gross_realized_pnl"] == 10.0
    assert out["summary"]["total_fees"] == 3.0
    assert out["summary"]["net_realized_pnl"] == 7.0
    assert len(out["closed_trades"]) == 1
    assert out["closed_trades"][0]["fees"] == 3.0

