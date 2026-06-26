from __future__ import annotations

from services.backtest.leaderboard import (
    COMPOSITE_HYBRID_RESEARCH_CANDIDATE,
    default_strategy_candidates,
    rank_strategy_rows,
    run_strategy_leaderboard,
)
from services.strategies.composite_hybrid import MODE_CONFIRMATION_GATE, STRATEGY_ID
from services.strategies.strategy_registry import SUPPORTED


def _candles(closes: list[float]) -> list[list[float]]:
    rows: list[list[float]] = []
    if not closes:
        return rows
    prev = float(closes[0])
    for i, close in enumerate(closes):
        c = float(close)
        o = float(prev)
        h = max(o, c) + 0.2
        low = min(o, c) - 0.2
        rows.append([i * 60_000, o, h, low, c, 1.0])
        prev = c
    return rows


def test_default_strategy_candidates_returns_supported_defaults():
    out = default_strategy_candidates({"risk": {"max_order_quote": 25.0}})

    assert [row["candidate"] for row in out] == [
        "ema_cross_default",
        "mean_reversion_default",
        "breakout_default",
        COMPOSITE_HYBRID_RESEARCH_CANDIDATE,
        "momentum_default",
        "pullback_recovery_default",
        "sma_200_trend_default",
        "volatility_reversal_default",
        "gap_fill_default",
        "breakout_volume_default",
    ]
    assert out[0]["cfg"]["risk"]["max_order_quote"] == 25.0


def test_default_strategy_candidates_includes_research_only_composite_without_runtime_registration():
    out = default_strategy_candidates({"risk": {"max_order_quote": 25.0}})
    row = next(item for item in out if item["candidate"] == COMPOSITE_HYBRID_RESEARCH_CANDIDATE)
    strategy = row["cfg"]["strategy"]

    assert strategy["name"] == STRATEGY_ID
    assert strategy["mode"] == MODE_CONFIRMATION_GATE
    assert strategy["research_only"] is True
    assert strategy["primary"]["name"] == "breakout_donchian"
    assert strategy["confirmer"]["name"] == "sma_200_trend"
    assert STRATEGY_ID not in SUPPORTED


def test_leaderboard_backtest_does_not_write_runtime_signal_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    prices = [100.0 + (idx * 0.1) for idx in range(230)]
    out = run_strategy_leaderboard(
        base_cfg={},
        symbol="BTC/USDT",
        candles=_candles(prices),
        warmup_bars=200,
        initial_cash=1_000.0,
        fee_bps=10.0,
        slippage_bps=5.0,
    )

    evidence_dir = tmp_path / "data" / "evidence" / "es_daily_trend_v1"
    assert out["ok"] is True
    assert not list(evidence_dir.glob("signal_*.jsonl"))


def test_rank_strategy_rows_penalizes_drawdown_and_drift():
    ranked = rank_strategy_rows(
        [
            {
                "candidate": "steady",
                "strategy": "ema_cross",
                "net_return_after_costs_pct": 8.0,
                "max_drawdown_pct": 3.0,
                "regime_robustness": 0.8,
                "regime_return_dispersion_pct": 1.0,
                "slippage_sensitivity_pct": 0.5,
                "paper_live_drift_pct": 0.0,
                "closed_trades": 4,
                "exposure_fraction": 0.25,
            },
            {
                "candidate": "fragile",
                "strategy": "ema_cross",
                "net_return_after_costs_pct": 9.0,
                "max_drawdown_pct": 15.0,
                "regime_robustness": 0.4,
                "regime_return_dispersion_pct": 8.0,
                "slippage_sensitivity_pct": 4.0,
                "paper_live_drift_pct": 6.0,
                "closed_trades": 4,
                "exposure_fraction": 0.25,
            },
        ]
    )

    assert ranked[0]["candidate"] == "steady"
    assert ranked[0]["leaderboard_score"] > ranked[1]["leaderboard_score"]
    assert ranked[0]["rank"] == 1
    assert ranked[1]["rank"] == 2


def test_rank_strategy_rows_penalizes_zero_trade_inactivity():
    ranked = rank_strategy_rows(
        [
            {
                "candidate": "inactive",
                "strategy": "mean_reversion_rsi",
                "net_return_after_costs_pct": 0.0,
                "max_drawdown_pct": 0.0,
                "regime_robustness": 1.0,
                "regime_return_dispersion_pct": 0.0,
                "slippage_sensitivity_pct": 0.0,
                "paper_live_drift_pct": 0.0,
                "closed_trades": 0,
                "exposure_fraction": 0.0,
            },
            {
                "candidate": "active",
                "strategy": "breakout_donchian",
                "net_return_after_costs_pct": 6.0,
                "max_drawdown_pct": 2.0,
                "regime_robustness": 0.8,
                "regime_return_dispersion_pct": 1.5,
                "slippage_sensitivity_pct": 0.4,
                "paper_live_drift_pct": 0.2,
                "closed_trades": 3,
                "exposure_fraction": 0.25,
            },
        ]
    )

    assert ranked[0]["candidate"] == "active"
    assert ranked[1]["candidate"] == "inactive"
    assert ranked[1]["leaderboard_components"]["participation_component"] == 0.0
    assert ranked[1]["leaderboard_components"]["thin_sample_penalty"] > 0.0


def test_rank_strategy_rows_penalizes_thin_participation():
    ranked = rank_strategy_rows(
        [
            {
                "candidate": "thin",
                "strategy": "ema_cross",
                "net_return_after_costs_pct": 10.0,
                "max_drawdown_pct": 4.0,
                "regime_robustness": 0.7,
                "regime_return_dispersion_pct": 2.0,
                "slippage_sensitivity_pct": 0.6,
                "paper_live_drift_pct": 0.4,
                "closed_trades": 1,
                "exposure_fraction": 0.08,
            },
            {
                "candidate": "proven",
                "strategy": "breakout_donchian",
                "net_return_after_costs_pct": 10.0,
                "max_drawdown_pct": 4.0,
                "regime_robustness": 0.7,
                "regime_return_dispersion_pct": 2.0,
                "slippage_sensitivity_pct": 0.6,
                "paper_live_drift_pct": 0.4,
                "closed_trades": 4,
                "exposure_fraction": 0.25,
            },
        ]
    )

    assert ranked[0]["candidate"] == "proven"
    assert ranked[1]["candidate"] == "thin"
    assert ranked[0]["leaderboard_score"] > ranked[1]["leaderboard_score"]
    assert ranked[1]["leaderboard_components"]["thin_sample_penalty"] > 0.0


def test_run_strategy_leaderboard_returns_ranked_rows():
    prices = [
        100,
        99,
        98,
        97,
        96,
        95,
        94,
        93,
        92,
        91,
        90,
        91,
        92,
        93,
        94,
        95,
        96,
        97,
        98,
        99,
        100,
        101,
        102,
        103,
        104,
        105,
        106,
        107,
        108,
        109,
    ]
    out = run_strategy_leaderboard(
        base_cfg={},
        symbol="BTC/USD",
        candles=_candles(prices),
        warmup_bars=5,
        initial_cash=1_000.0,
        fee_bps=10.0,
        slippage_bps=5.0,
        paper_live_drifts={"ema_cross": 0.5, "mean_reversion_rsi": 2.0, "breakout_donchian": 1.0},
    )

    assert out["ok"] is True
    assert out["candidate_count"] == 10
    assert out["stressed_slippage_bps"] > out["base_slippage_bps"]
    assert len(out["rows"]) == 10
    assert out["rows"][0]["leaderboard_score"] >= out["rows"][-1]["leaderboard_score"]
    assert {"candidate", "strategy", "leaderboard_score", "slippage_sensitivity_pct", "regime_robustness", "closed_trades", "trade_count", "exposure_fraction"} <= set(
        out["rows"][0].keys()
    )


def test_run_strategy_leaderboard_surfaces_research_composite_candidate(monkeypatch):
    calls: list[str] = []

    def fake_run_parity_backtest(*, cfg, symbol, candles, warmup_bars, initial_cash, fee_bps, slippage_bps):
        strategy_name = str(cfg["strategy"]["name"])
        calls.append(strategy_name)
        return {
            "trade_count": 2,
            "scorecard": {
                "strategy": strategy_name,
                "net_return_after_costs_pct": 1.0,
                "max_drawdown_pct": 0.5,
                "expectancy": 0.25,
                "win_rate_pct": 50.0,
                "closed_trades": 1,
                "exposure_fraction": 0.1,
                "exposure_adjusted_return_pct": 10.0,
            },
            "regime_scorecards": {"all": {"bars": 3, "net_return_after_costs_pct": 1.0}},
        }

    monkeypatch.setattr("services.backtest.leaderboard.run_parity_backtest", fake_run_parity_backtest)

    out = run_strategy_leaderboard(
        base_cfg={},
        symbol="BTC/USD",
        candles=_candles([100.0, 101.0, 102.0]),
        warmup_bars=1,
        initial_cash=1_000.0,
        fee_bps=10.0,
        slippage_bps=5.0,
    )

    row = next(item for item in out["rows"] if item["candidate"] == COMPOSITE_HYBRID_RESEARCH_CANDIDATE)
    assert row["strategy"] == STRATEGY_ID
    assert calls.count(STRATEGY_ID) == 2
    assert STRATEGY_ID not in SUPPORTED
