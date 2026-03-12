from __future__ import annotations

from dashboard.components.summary_panels import (
    build_market_context_lines,
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


def test_build_market_context_lines_includes_snapshot_and_evidence() -> None:
    lines = build_market_context_lines(
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

    assert lines[0] == "Support: $89,196.92"
    assert lines[1] == "Resistance: $91,913.58"
    assert "Quote: Bid $90,550.00 | Ask $90,560.50 | Spread $10.50" in lines
    assert "Source: coinbase / local ws" in lines
    assert lines[-1] == "Evidence: Spot demand improved."
