from __future__ import annotations

from dashboard.components.asset_detail import build_asset_detail_metrics, build_focus_summary_metrics


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


def test_build_focus_summary_metrics_formats_signal_summary() -> None:
    metrics = build_focus_summary_metrics(
        {
            "signal": "buy",
            "status": "pending_review",
            "confidence": 0.81,
            "change_24h_pct": 6.5,
            "price": 200.0,
            "execution_disabled": True,
            "risk_note": "Research only.",
        }
    )

    assert metrics[0] == {
        "label": "Signal",
        "value": "Buy",
        "delta": "Pending Review",
    }
    assert metrics[1] == {
        "label": "Confidence",
        "value": "81%",
        "delta": "AI conviction",
    }
    assert metrics[2] == {
        "label": "24h Move",
        "value": "+6.5%",
        "delta": "$200.00",
    }
    assert metrics[3] == {
        "label": "Execution",
        "value": "Disabled",
        "delta": "Research only.",
    }
