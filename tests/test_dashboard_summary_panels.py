from __future__ import annotations

from dashboard.components.summary_panels import (
    build_market_context_metrics,
    build_market_snapshot_lines,
    build_portfolio_position_metrics,
    build_trades_queue_metrics,
    resolve_asset_row,
)


def test_resolve_asset_row_returns_matching_asset() -> None:
    rows = [
        {"asset": "BTC", "summary": "Range trade"},
        {"asset": "SOL", "summary": "Momentum"},
    ]
    payload = resolve_asset_row(rows, asset="SOL")
    assert payload["summary"] == "Momentum"


def test_resolve_asset_row_returns_empty_dict_when_missing() -> None:
    rows = [{"asset": "BTC", "summary": "Range trade"}]
    payload = resolve_asset_row(rows, asset="ETH")
    assert payload == {}


def test_build_market_snapshot_lines_formats_quote_and_source() -> None:
    lines = build_market_snapshot_lines(
        {
            "price": 90555.25,
            "bid": 90550.0,
            "ask": 90560.5,
            "spread": 10.5,
            "exchange": "coinbase",
            "snapshot_source": "api",
            "snapshot_timestamp": "2026-03-11T12:55:00Z",
        },
        include_price=True,
    )

    assert lines[0] == "Spot: $90,555.25"
    assert lines[1] == "Quote: Bid $90,550.00 | Ask $90,560.50 | Spread $10.50"
    assert lines[2] == "Source: coinbase / api | 2026-03-11T12:55:00Z"


def test_build_market_context_metrics_include_snapshot_metadata() -> None:
    metrics = build_market_context_metrics(
        {
            "support": 89196.92,
            "resistance": 91913.58,
            "bid": 90550.0,
            "ask": 90560.5,
            "spread": 10.5,
            "exchange": "coinbase",
            "snapshot_source": "local_ws",
            "evidence": "Spot demand improved.",
        }
    )

    assert metrics[0] == {
        "label": "Support",
        "value": "$89,196.92",
        "delta": "buy-side reference",
    }
    assert metrics[1] == {
        "label": "Resistance",
        "value": "$91,913.58",
        "delta": "sell-side reference",
    }
    assert metrics[2] == {
        "label": "Bid / Ask",
        "value": "$90,550.00 / $90,560.50",
        "delta": "Spread $10.50",
    }
    assert metrics[3] == {
        "label": "Source",
        "value": "Local Ws",
        "delta": "coinbase",
    }


def test_build_portfolio_position_metrics_formats_best_and_worst_positions() -> None:
    metrics = build_portfolio_position_metrics(
        [
            {"asset": "BTC", "side": "long", "pnl": 495.6},
            {"asset": "SOL", "side": "long", "pnl": 630.9},
            {"asset": "ETH", "side": "short", "pnl": -120.5},
        ]
    )

    assert metrics[0] == {
        "label": "Open Positions",
        "value": "3",
        "delta": "Active book",
    }
    assert metrics[1] == {
        "label": "Long / Short",
        "value": "2 / 1",
        "delta": "Position mix",
    }
    assert metrics[2] == {
        "label": "Best PnL",
        "value": "$630.90",
        "delta": "SOL",
    }
    assert metrics[3] == {
        "label": "Worst PnL",
        "value": "$-120.50",
        "delta": "ETH",
    }


def test_build_trades_queue_metrics_formats_queue_and_fill_details() -> None:
    metrics = build_trades_queue_metrics(
        [
            {"asset": "SOL", "side": "buy", "risk_size_pct": 1.5},
            {"asset": "BTC", "side": "sell", "risk_size_pct": 0.8},
        ],
        [
            {"asset": "ETH", "side": "sell", "qty": 0.3, "price": 4390.0},
        ],
    )

    assert metrics[0] == {
        "label": "Approval Mix",
        "value": "1 / 1",
        "delta": "Buy / Sell",
    }
    assert metrics[1] == {
        "label": "Largest Review",
        "value": "1.5%",
        "delta": "SOL",
    }
    assert metrics[2] == {
        "label": "Last Fill Price",
        "value": "$4,390.00",
        "delta": "ETH",
    }
    assert metrics[3] == {
        "label": "Last Fill Qty",
        "value": "0.3",
        "delta": "SELL",
    }
