from __future__ import annotations

from dashboard.services import strategy_evaluation as eval_service


def test_build_strategy_workbench_aggregates_backtest_leaderboard_and_hypothesis(monkeypatch) -> None:
    monkeypatch.setattr(
        eval_service,
        "run_parity_backtest",
        lambda **kwargs: {"ok": True, "strategy": "ema_cross", "scorecard": {"closed_trades": 4}},
    )
    monkeypatch.setattr(
        eval_service,
        "run_strategy_leaderboard",
        lambda **kwargs: {"ok": True, "candidate_count": 3, "rows": [{"candidate": "ema_cross_default"}]},
    )
    monkeypatch.setattr(
        eval_service,
        "get_strategy_hypothesis",
        lambda name: {"strategy": name, "market_assumption": "trend persistence"},
    )

    out = eval_service.build_strategy_workbench(
        cfg={"strategy": {"name": "ema_cross"}},
        strategy_name="ema_cross",
        symbol="BTC/USD",
        candles=[[1, 1, 1, 1, 1, 1]],
    )

    assert out["ok"] is True
    assert out["backtest"]["strategy"] == "ema_cross"
    assert out["leaderboard"]["candidate_count"] == 3
    assert out["hypothesis"]["strategy"] == "ema_cross"
    assert out["research_only"] is True
    assert out["execution_enabled"] is False


def test_build_scorecard_and_regime_rows_format_metrics() -> None:
    scorecard_rows = eval_service.build_scorecard_table_rows(
        {
            "net_return_after_costs_pct": 12.3456,
            "max_drawdown_pct": 3.21,
            "profit_factor": 1.75,
            "sharpe_ratio": 0.8,
            "sortino_ratio": 1.2,
            "win_rate_pct": 66.0,
            "expectancy": 4.5,
            "exposure_adjusted_return_pct": 18.2,
            "total_fees": 12.0,
            "closed_trades": 8,
            "paper_live_drift_pct": None,
            "operational_incidents": 0,
        }
    )
    regime_rows = eval_service.build_regime_table_rows(
        {
            "bull": {"bars": 10, "net_return_after_costs_pct": 4.2, "max_drawdown_pct": 1.1, "win_rate_pct": 60.0, "profit_factor": 1.4, "expectancy": 2.0, "closed_trades": 3},
            "chop": {"bars": 0},
        }
    )

    assert scorecard_rows[0]["metric"] == "Net Return After Costs"
    assert scorecard_rows[0]["value"] == "12.35%"
    assert any(row["metric"] == "Paper/Live Drift" and row["value"] == "-" for row in scorecard_rows)
    assert regime_rows == [
        {
            "regime": "Bull",
            "bars": 10,
            "return_pct": 4.2,
            "max_drawdown_pct": 1.1,
            "win_rate_pct": 60.0,
            "profit_factor": 1.4,
            "expectancy": 2.0,
            "closed_trades": 3,
        }
    ]


def test_build_leaderboard_and_hypothesis_rows_are_ui_ready() -> None:
    leaderboard_rows = eval_service.build_leaderboard_table_rows(
        {
            "rows": [
                {
                    "rank": 1,
                    "candidate": "ema_cross_default",
                    "strategy": "ema_cross",
                    "leaderboard_score": 0.81234,
                    "net_return_after_costs_pct": 11.2,
                    "max_drawdown_pct": 3.6,
                    "regime_robustness": 0.75,
                    "regime_return_dispersion_pct": 2.8,
                    "slippage_sensitivity_pct": 1.1,
                    "paper_live_drift_pct": None,
                }
            ]
        }
    )
    sections = eval_service.build_hypothesis_sections(
        {
            "market_assumption": "trend persistence",
            "entry_rules": ["cross up"],
            "exit_rules": ["cross down"],
            "no_trade_rules": ["weak volume"],
            "invalidation_conditions": ["wrong-side slow ema"],
            "expected_failure_regimes": ["low_vol"],
            "notes": ["not proven"],
        }
    )

    assert leaderboard_rows[0]["candidate"] == "ema_cross_default"
    assert leaderboard_rows[0]["leaderboard_score"] == 0.8123
    assert sections[0]["title"] == "Market Assumption"
    assert sections[5]["items"] == ["Low Vol"]
