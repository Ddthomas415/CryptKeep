from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml


def _router_cfg(strategy: str = "es_daily_trend", **overrides):
    from services.pipeline.pipeline_router import RouterCfg

    defaults = dict(
        exec_db=":memory:",
        exchange_id="coinbase",
        symbol="BTC/USD",
        timeframe="5m",
        ohlcv_limit=100,
        mode="paper",
        fixed_qty=0.0,
        quote_notional=100.0,
        only_on_new_bar=True,
        strategy=strategy,
    )
    defaults.update(overrides)
    return RouterCfg(**defaults)


def _make_ohlcv(n: int, close: float = 60000.0):
    return [[i * 86400000, close, close, close, close, 1000.0] for i in range(n)]


def _mock_pipeline_deps(p):
    p.state = MagicMock()
    p.ops = MagicMock()
    p.md = MagicMock()
    p.writer = MagicMock()
    p.state.get.return_value = {}
    p.writer.create_intent.return_value = "intent-001"
    return p


def test_build_pipeline_returns_es_daily_trend_pipeline():
    from services.pipeline.pipeline_router import build_pipeline
    from services.pipeline.es_daily_trend_pipeline import ESDailyTrendPipeline

    with patch("services.pipeline.es_daily_trend_pipeline.CCXTMarketData"), \
         patch("services.pipeline.es_daily_trend_pipeline.StrategyStateStore"), \
         patch("services.pipeline.es_daily_trend_pipeline.OpsEventStore"), \
         patch("services.pipeline.es_daily_trend_pipeline.IntentWriter"):
        p = build_pipeline(_router_cfg())

    assert isinstance(p, ESDailyTrendPipeline)


def test_es_daily_trend_enforces_1d_and_min_bars():
    from services.pipeline.pipeline_router import build_pipeline

    with patch("services.pipeline.es_daily_trend_pipeline.CCXTMarketData"), \
         patch("services.pipeline.es_daily_trend_pipeline.StrategyStateStore"), \
         patch("services.pipeline.es_daily_trend_pipeline.OpsEventStore"), \
         patch("services.pipeline.es_daily_trend_pipeline.IntentWriter"):
        p = build_pipeline(_router_cfg(timeframe="5m", ohlcv_limit=50))

    assert p.cfg.timeframe == "1d"
    assert p.cfg.ohlcv_limit >= 220


def test_run_once_returns_no_new_bar_on_same_bar():
    from services.pipeline.es_daily_trend_pipeline import ESDailyTrendCfg, ESDailyTrendPipeline

    with patch("services.pipeline.es_daily_trend_pipeline.CCXTMarketData"), \
         patch("services.pipeline.es_daily_trend_pipeline.StrategyStateStore"), \
         patch("services.pipeline.es_daily_trend_pipeline.OpsEventStore"), \
         patch("services.pipeline.es_daily_trend_pipeline.IntentWriter"):
        p = ESDailyTrendPipeline(ESDailyTrendCfg(exec_db=":memory:", exchange_id="coinbase", symbol="BTC/USD", mode="paper"))

    _mock_pipeline_deps(p)
    ohlcv = _make_ohlcv(220)
    p.md.ohlcv.return_value = ohlcv
    p.state.get.return_value = {"last_bar_ts_ms": ohlcv[-1][0]}

    assert p.run_once()["note"] == "no_new_bar"


def test_run_once_returns_not_enough_data():
    from services.pipeline.es_daily_trend_pipeline import ESDailyTrendCfg, ESDailyTrendPipeline

    with patch("services.pipeline.es_daily_trend_pipeline.CCXTMarketData"), \
         patch("services.pipeline.es_daily_trend_pipeline.StrategyStateStore"), \
         patch("services.pipeline.es_daily_trend_pipeline.OpsEventStore"), \
         patch("services.pipeline.es_daily_trend_pipeline.IntentWriter"):
        p = ESDailyTrendPipeline(ESDailyTrendCfg(exec_db=":memory:", exchange_id="coinbase", symbol="BTC/USD", mode="paper"))

    _mock_pipeline_deps(p)
    p.md.ohlcv.return_value = _make_ohlcv(100)

    out = p.run_once()
    assert out["ok"] is False
    assert out["note"] == "not_enough_data"
    assert out["required"] == 220


def test_run_once_creates_intent_on_buy_signal():
    from services.pipeline.es_daily_trend_pipeline import ESDailyTrendCfg, ESDailyTrendPipeline

    with patch("services.pipeline.es_daily_trend_pipeline.CCXTMarketData"), \
         patch("services.pipeline.es_daily_trend_pipeline.StrategyStateStore"), \
         patch("services.pipeline.es_daily_trend_pipeline.OpsEventStore"), \
         patch("services.pipeline.es_daily_trend_pipeline.IntentWriter"):
        p = ESDailyTrendPipeline(ESDailyTrendCfg(exec_db=":memory:", exchange_id="coinbase", symbol="BTC/USD", mode="paper", quote_notional=100.0))

    _mock_pipeline_deps(p)
    p.md.ohlcv.return_value = _make_ohlcv(220)
    p.state.get.return_value = {}

    with patch("services.pipeline.es_daily_trend_pipeline.signal_from_ohlcv", return_value={
        "ok": True,
        "action": "buy",
        "reason": "sma200:long",
        "regime": "trending",
        "sma_200": 59000.0,
        "atr_ratio": 0.02,
        "entry_allowed": True,
    }):
        out = p.run_once()

    assert out["ok"] is True
    assert out["note"] == "intent_created"
    p.writer.create_intent.assert_called_once()
    assert p.writer.create_intent.call_args.kwargs["strategy_id"] == "es_daily_trend_v1"


def test_run_once_does_not_update_state_when_create_intent_fails():
    from services.pipeline.es_daily_trend_pipeline import ESDailyTrendCfg, ESDailyTrendPipeline

    with patch("services.pipeline.es_daily_trend_pipeline.CCXTMarketData"), \
         patch("services.pipeline.es_daily_trend_pipeline.StrategyStateStore"), \
         patch("services.pipeline.es_daily_trend_pipeline.OpsEventStore"), \
         patch("services.pipeline.es_daily_trend_pipeline.IntentWriter"):
        p = ESDailyTrendPipeline(ESDailyTrendCfg(exec_db=":memory:", exchange_id="coinbase", symbol="BTC/USD", mode="paper", quote_notional=100.0))

    _mock_pipeline_deps(p)
    p.md.ohlcv.return_value = _make_ohlcv(220)
    p.writer.create_intent.side_effect = RuntimeError("db write failed")

    with patch("services.pipeline.es_daily_trend_pipeline.signal_from_ohlcv", return_value={
        "ok": True,
        "action": "buy",
        "reason": "sma200:long",
    }):
        with pytest.raises(RuntimeError):
            p.run_once()

    p.state.upsert.assert_not_called()


def test_config_default_remains_ema_with_es_params_present():
    cfg = yaml.safe_load(Path("config/trading.yaml").read_text())
    pipe = cfg.get("pipeline")

    assert isinstance(pipe, dict)
    assert pipe["strategy"] == "ema"
    assert "sma_period" in pipe
    assert "atr_period" in pipe


def test_build_pipeline_still_returns_ema_for_ema_strategy():
    from services.pipeline.pipeline_router import build_pipeline
    from services.pipeline.ema_strategy import EMACrossoverPipeline

    with patch("services.pipeline.ema_strategy.CCXTMarketData"), \
         patch("services.pipeline.ema_strategy.StrategyStateStore"), \
         patch("services.pipeline.ema_strategy.OpsEventStore"), \
         patch("services.pipeline.ema_strategy.IntentWriter"):
        p = build_pipeline(_router_cfg(strategy="ema"))

    assert isinstance(p, EMACrossoverPipeline)
