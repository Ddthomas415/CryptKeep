from __future__ import annotations

from services.backtest.scorecard import build_strategy_scorecard, scorecard_row


def test_build_strategy_scorecard_computes_core_metrics():
    trades = [
        {"ts_ms": 60_000, "action": "buy", "fee": 1.0},
        {"ts_ms": 120_000, "action": "sell", "fee": 1.0, "realized_pnl": 30.0},
        {"ts_ms": 180_000, "action": "buy", "fee": 1.0},
        {"ts_ms": 240_000, "action": "sell", "fee": 1.0, "realized_pnl": -10.0},
    ]
    equity = [
        {"ts_ms": 0, "equity": 1000.0, "pos_qty": 0.0},
        {"ts_ms": 60_000, "equity": 1030.0, "pos_qty": 1.0},
        {"ts_ms": 120_000, "equity": 1015.0, "pos_qty": 0.0},
        {"ts_ms": 180_000, "equity": 1025.0, "pos_qty": 1.0},
        {"ts_ms": 240_000, "equity": 1020.0, "pos_qty": 0.0},
    ]

    out = build_strategy_scorecard(
        strategy="ema_cross",
        symbol="BTC/USD",
        trades=trades,
        equity=equity,
        initial_cash=1000.0,
        fee_bps=10.0,
        slippage_bps=5.0,
        paper_return_pct=1.2,
        live_return_pct=0.7,
        operational_incidents=2,
    )

    assert out["strategy"] == "ema_cross"
    assert out["symbol"] == "BTC/USD"
    assert out["closed_trades"] == 2
    assert round(float(out["net_return_after_costs_pct"]), 2) == 2.0
    assert round(float(out["max_drawdown_pct"]), 2) == 1.46
    assert float(out["profit_factor"]) == 3.0
    assert float(out["win_rate_pct"]) == 50.0
    assert float(out["avg_win"]) == 30.0
    assert float(out["avg_loss"]) == -10.0
    assert float(out["expectancy"]) == 10.0
    assert float(out["exposure_fraction"]) == 0.4
    assert round(float(out["exposure_adjusted_return_pct"]), 2) == 5.0
    assert float(out["paper_live_drift_pct"]) == -0.5
    assert int(out["operational_incidents"]) == 2
    assert float(out["total_fees"]) == 4.0


def test_scorecard_row_flattens_for_comparison():
    row = scorecard_row(
        {
            "strategy": "breakout_donchian",
            "symbol": "ETH/USD",
            "net_return_after_costs_pct": 3.5,
            "max_drawdown_pct": 1.2,
            "profit_factor": 1.8,
            "sharpe_ratio": 0.9,
            "sortino_ratio": 1.1,
            "win_rate_pct": 60.0,
            "expectancy": 4.2,
            "exposure_adjusted_return_pct": 5.0,
            "paper_live_drift_pct": None,
            "operational_incidents": 1,
            "closed_trades": 5,
        }
    )

    assert row == {
        "strategy": "breakout_donchian",
        "symbol": "ETH/USD",
        "net_return_after_costs_pct": 3.5,
        "max_drawdown_pct": 1.2,
        "profit_factor": 1.8,
        "sharpe_ratio": 0.9,
        "sortino_ratio": 1.1,
        "win_rate_pct": 60.0,
        "expectancy": 4.2,
        "exposure_adjusted_return_pct": 5.0,
        "paper_live_drift_pct": None,
        "operational_incidents": 1,
        "closed_trades": 5,
    }
