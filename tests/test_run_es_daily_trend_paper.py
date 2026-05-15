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
