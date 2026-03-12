from __future__ import annotations

from dashboard.components.summary_panels import (
    build_market_context_metrics,
    build_market_snapshot_lines,
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
