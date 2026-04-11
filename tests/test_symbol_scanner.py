from __future__ import annotations

from services.market_data.symbol_scanner import _rsi, _safe


def test_safe_handles_bad_values() -> None:
    assert _safe("abc", 1.23) == 1.23
    assert _safe(None, 2.34) == 2.34
    assert _safe("5.5", 0.0) == 5.5


def test_rsi_returns_none_when_not_enough_data() -> None:
    assert _rsi([1.0, 2.0, 3.0], period=14) is None


def test_rsi_returns_high_for_monotonic_uptrend() -> None:
    closes = [float(i) for i in range(1, 30)]
    val = _rsi(closes, period=14)
    assert val is not None
    assert val > 70


def test_rsi_returns_low_for_monotonic_downtrend() -> None:
    closes = [float(i) for i in range(30, 1, -1)]
    val = _rsi(closes, period=14)
    assert val is not None
    assert val < 30
