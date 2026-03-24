from pathlib import Path


def test_startup_guard_is_wired_into_live_runner() -> None:
    runner = Path("services/strategy_runner/ema_crossover_runner.py").read_text()
    guard = Path("services/strategy/startup_guard.py").read_text()

    assert "require_known_flat_or_override" in runner
    assert "require_known_flat_or_override" in guard
    assert "unknown_position_state" in guard
    assert "open_position_requires_override" in guard
