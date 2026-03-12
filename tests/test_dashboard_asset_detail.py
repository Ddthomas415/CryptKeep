from __future__ import annotations

from dashboard.components.asset_detail import build_asset_detail_metrics


def test_build_asset_detail_metrics_formats_snapshot_row() -> None:
    metrics = build_asset_detail_metrics(
        {
            "price": 90555.25,
            "bid": 90550.0,
            "ask": 90560.5,
            "spread": 10.5,
            "exchange": "coinbase",
            "snapshot_source": "api",
            "snapshot_timestamp": "2026-03-11T12:55:00Z",
        }
    )

    assert metrics[0] == {"label": "Spot", "value": "$90,555.25", "delta": "coinbase"}
    assert metrics[1] == {
        "label": "Bid / Ask",
        "value": "$90,550.00 / $90,560.50",
        "delta": "",
    }
    assert metrics[2] == {"label": "Spread", "value": "$10.50", "delta": ""}
    assert metrics[3] == {
        "label": "Source",
        "value": "Api",
        "delta": "coinbase / 2026-03-11T12:55:00Z",
    }


def test_build_asset_detail_metrics_handles_missing_quote_values() -> None:
    metrics = build_asset_detail_metrics({"price": 200.0, "snapshot_source": "watchlist"})

    assert metrics[0]["value"] == "$200.00"
    assert metrics[1]["value"] == "- / -"
    assert metrics[2]["value"] == "-"
    assert metrics[3]["value"] == "Watchlist"
