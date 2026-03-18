from __future__ import annotations

from services.analytics.crypto_edges import (
    build_crypto_edge_report,
    summarize_basis_spread,
    summarize_cross_venue_dislocations,
    summarize_funding_carry,
)


def test_summarize_funding_carry_computes_bias_and_annualization():
    out = summarize_funding_carry(
        [
            {"symbol": "BTC-PERP", "venue": "venue_a", "funding_rate": 0.0001},
            {"symbol": "BTC-PERP", "venue": "venue_a", "funding_rate": 0.0002},
            {"symbol": "BTC-PERP", "venue": "venue_a", "funding_rate": -0.00005},
        ],
        interval_hours=8.0,
    )

    assert out["ok"] is True
    assert out["count"] == 3
    assert out["dominant_bias"] == "long_pays"
    assert out["annualized_carry_pct"] > 0.0
    assert out["rows"][0]["side_bias"] == "long_pays"


def test_summarize_basis_spread_marks_premium_and_discount():
    out = summarize_basis_spread(
        [
            {"symbol": "BTC", "venue": "venue_a", "spot_px": 100.0, "perp_px": 101.0},
            {"symbol": "ETH", "venue": "venue_b", "spot_px": 100.0, "perp_px": 99.0},
        ]
    )

    assert out["ok"] is True
    assert out["count"] == 2
    assert out["premium_ratio"] == 0.5
    assert out["discount_ratio"] == 0.5
    assert {row["basis_state"] for row in out["rows"]} == {"premium", "discount"}


def test_summarize_cross_venue_dislocations_finds_positive_cross():
    out = summarize_cross_venue_dislocations(
        [
            {"symbol": "BTC/USD", "venue": "venue_a", "bid": 101.0, "ask": 101.5},
            {"symbol": "BTC/USD", "venue": "venue_b", "bid": 100.0, "ask": 100.2},
            {"symbol": "ETH/USD", "venue": "venue_c", "bid": 50.0, "ask": 50.1},
        ]
    )

    assert out["ok"] is True
    assert out["count"] == 2
    assert out["positive_count"] >= 1
    assert out["top_dislocation"] is not None
    assert out["top_dislocation"]["symbol"] == "BTC/USD"
    assert out["top_dislocation"]["gross_cross_bps"] > 0.0


def test_build_crypto_edge_report_stays_research_only():
    out = build_crypto_edge_report(
        funding_rows=[{"symbol": "BTC-PERP", "venue": "venue_a", "funding_rate": 0.0001}],
        basis_rows=[{"symbol": "BTC", "venue": "venue_a", "spot_px": 100.0, "perp_px": 100.5}],
        quote_rows=[{"symbol": "BTC/USD", "venue": "venue_a", "bid": 101.0, "ask": 100.5}],
    )

    assert out["ok"] is True
    assert out["research_only"] is True
    assert out["execution_enabled"] is False
    assert out["funding"]["count"] == 1
    assert out["basis"]["count"] == 1
    assert out["dislocations"]["count"] == 1
