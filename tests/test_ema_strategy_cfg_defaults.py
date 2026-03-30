from services.pipeline.ema_strategy import EMAStrategyCfg


def test_ema_strategy_cfg_has_no_silent_runtime_defaults():
    cfg = EMAStrategyCfg()
    assert cfg.exchange_id == ""
    assert cfg.symbol == ""
    assert cfg.mode == ""


def test_pipeline_cfg_can_still_be_set_explicitly():
    cfg = EMAStrategyCfg(
        exchange_id="coinbase",
        symbol="BTC/USD",
        mode="paper",
    )
    assert cfg.exchange_id == "coinbase"
    assert cfg.symbol == "BTC/USD"
    assert cfg.mode == "paper"
