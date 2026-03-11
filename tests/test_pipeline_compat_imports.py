from __future__ import annotations

import importlib


def test_pipeline_compat_modules_import():
    modules = [
        "services.pipeline.mean_reversion_strategy",
        "services.pipeline.pipeline_router",
        "services.market_data.ccxt_market_data",
        "services.execution.intent_writer",
    ]

    for name in modules:
        mod = importlib.import_module(name)
        assert mod is not None


def test_ema_pipeline_creates_intent(tmp_path):
    from services.pipeline.ema_strategy import EMACrossoverPipeline, EMAStrategyCfg
    from storage.ops_event_store_sqlite import OpsEventStore
    from storage.strategy_state_store_sqlite import StrategyStateStore

    exec_db = tmp_path / "exec.sqlite"
    pipeline = EMACrossoverPipeline(
        EMAStrategyCfg(
            exec_db=str(exec_db),
            exchange_id="coinbase",
            symbol="BTC-USD",
            timeframe="1h",
            fast=2,
            slow=3,
            fixed_qty=1.5,
        )
    )

    class FakeMD:
        def ohlcv(self, symbol: str, timeframe: str, limit: int = 500) -> list[list]:
            return [
                [1, 0, 0, 0, 105.0, 0],
                [2, 0, 0, 0, 103.0, 0],
                [3, 0, 0, 0, 101.0, 0],
                [4, 0, 0, 0, 99.0, 0],
                [5, 0, 0, 0, 101.0, 0],
                [6, 0, 0, 0, 105.0, 0],
            ]

    pipeline.md = FakeMD()

    out = pipeline.run_once()

    st = StrategyStateStore(str(exec_db)).get(
        strategy_id=pipeline.STRATEGY_ID,
        exchange="coinbase",
        symbol="BTC-USD",
        timeframe="1h",
    )
    ops = OpsEventStore(str(exec_db)).list_recent()

    assert out["ok"] is True
    assert out["note"] == "intent_created"
    assert out["qty"] == 1.5
    assert st is not None
    assert st["last_intent_id"] == out["intent_id"]
    assert ops[0]["event_type"] == "pipeline_intent_created"
