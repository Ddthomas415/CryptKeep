from __future__ import annotations

from scripts import run_es_daily_trend_paper as script


def test_build_campaign_cfg_enables_first_signal_trade(monkeypatch) -> None:
    monkeypatch.delenv("CBP_PAPER_RUNTIME_SEC", raising=False)

    cfg = script._build_campaign_cfg(
        {"paper_runtime_sec": 90},
        symbol="BTC/USDT",
        venue="coinbase",
    )

    assert cfg.strategies == ("sma_200_trend",)
    assert cfg.symbol == "BTC/USDT"
    assert cfg.venue == "coinbase"
    assert cfg.per_strategy_runtime_sec == 90.0
    assert cfg.signal_source == "public_ohlcv_1d"
    assert cfg.allow_first_signal_trade is True


def test_build_campaign_cfg_honors_runtime_override(monkeypatch) -> None:
    monkeypatch.setenv("CBP_PAPER_RUNTIME_SEC", "30")

    cfg = script._build_campaign_cfg(
        {"paper_runtime_sec": 90},
        symbol="BTC/USDT",
        venue="coinbase",
    )

    assert cfg.per_strategy_runtime_sec == 30.0
    assert cfg.allow_first_signal_trade is True


def test_apply_strategy_runtime_env_sets_first_signal_trade(monkeypatch) -> None:
    monkeypatch.delenv("CBP_DAILY_LOSS_HALT_PCT", raising=False)
    monkeypatch.delenv("CBP_SYMBOLS", raising=False)
    monkeypatch.delenv("CBP_VENUE", raising=False)
    monkeypatch.delenv("CBP_STRATEGY_ALLOW_FIRST_SIGNAL_TRADE", raising=False)
    monkeypatch.delenv("CBP_USE_CANDIDATE_ADVISOR", raising=False)

    script._apply_strategy_runtime_env(
        {"use_candidate_advisor": "yes"},
        {"daily_loss_halt_pct": 2.5},
        symbol="BTC/USDT",
        venue="coinbase",
    )

    assert script.os.environ["CBP_DAILY_LOSS_HALT_PCT"] == "2.5"
    assert script.os.environ["CBP_SYMBOLS"] == "BTC/USDT"
    assert script.os.environ["CBP_VENUE"] == "coinbase"
    assert script.os.environ["CBP_STRATEGY_ALLOW_FIRST_SIGNAL_TRADE"] == "1"
    assert script.os.environ["CBP_USE_CANDIDATE_ADVISOR"] == "1"
