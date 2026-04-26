from pathlib import Path


def test_ema_runner_exit_defaults_prefer_strategy_risk_config():
    text = Path("services/strategy_runner/ema_crossover_runner.py").read_text()

    assert 'risk_cfg = cfg.get("risk") if isinstance(cfg.get("risk"), dict) else {}' in text
    assert 'cfg.setdefault("max_bars_hold", risk_cfg.get("max_bars_hold", 60))' in text
    assert 'cfg.setdefault("stop_loss_pct", risk_cfg.get("stop_loss_pct", 0.03))' in text
    assert 'cfg.setdefault("take_profit_pct", risk_cfg.get("take_profit_pct", 0.06))' in text
    assert 'cfg.setdefault("trailing_stop_pct", risk_cfg.get("trailing_stop_pct", 0.02))' in text
