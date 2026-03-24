from pathlib import Path


def test_ema_cross_uses_canonical_helpers() -> None:
    text = Path("services/strategies/ema_cross.py").read_text()
    assert "canonical_compute_signal" in text
    assert "update_ema_state" in text
    assert "EMACfg" in text
    assert "EMAState" in text


def test_strategy_ema_is_wrapper_over_canonical_helpers() -> None:
    text = Path("services/strategy_ema.py").read_text()
    assert "update_ema_state" in text
    assert "compute_signal" in text
    assert "EMACrossStrategy" in text


def test_live_runner_no_local_ema_helper() -> None:
    text = Path("services/strategy_runner/ema_crossover_runner.py").read_text()
    assert "def _ema(" not in text
