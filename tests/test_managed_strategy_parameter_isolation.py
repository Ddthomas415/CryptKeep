from services.execution import strategy_runner as runner


def test_managed_es_does_not_inherit_momentum_period(monkeypatch):
    monkeypatch.setenv("CBP_STRATEGY_NAME", "sma_200_trend")
    monkeypatch.delenv("CBP_STRATEGY_PRESET", raising=False)
    block, preset = runner._strategy_block_from_runner_cfg({
        "strategy": {"name": "momentum", "sma_period": 20},
        "strategy_preset": "momentum_default",
    })
    assert block["name"] == "sma_200_trend"
    assert block["sma_period"] == 200
    assert preset == "es_daily_trend_v1"


def test_same_strategy_explicit_parameters_remain(monkeypatch):
    monkeypatch.setenv("CBP_STRATEGY_NAME", "sma_200_trend")
    monkeypatch.delenv("CBP_STRATEGY_PRESET", raising=False)
    block, _ = runner._strategy_block_from_runner_cfg({
        "strategy": {"name": "sma_200_trend", "sma_period": 150},
    })
    assert block["sma_period"] == 150


def test_switch_preserves_explicit_trade_disable(monkeypatch):
    monkeypatch.setenv("CBP_STRATEGY_NAME", "sma_200_trend")
    monkeypatch.delenv("CBP_STRATEGY_PRESET", raising=False)
    block, _ = runner._strategy_block_from_runner_cfg({
        "strategy": {"name": "momentum", "sma_period": 20, "trade_enabled": False},
    })
    assert block["sma_period"] == 200
    assert block["trade_enabled"] is False


def test_without_override_local_configuration_unchanged(monkeypatch):
    monkeypatch.delenv("CBP_STRATEGY_NAME", raising=False)
    monkeypatch.delenv("CBP_STRATEGY_PRESET", raising=False)
    block, _ = runner._strategy_block_from_runner_cfg({
        "strategy": {"name": "momentum", "sma_period": 20},
    })
    assert block["name"] == "momentum"
    assert block["sma_period"] == 20


def test_legacy_identity_switch_discards_local_parameters(monkeypatch):
    monkeypatch.setenv("CBP_STRATEGY_NAME", "ema_cross")
    monkeypatch.delenv("CBP_STRATEGY_PRESET", raising=False)
    block, _ = runner._strategy_block_from_runner_cfg({
        "strategy_name": "momentum", "fast_n": 99,
        "strategy": {"ema_slow": 101},
    })
    assert block["ema_fast"] != 99
    assert block["ema_slow"] != 101
