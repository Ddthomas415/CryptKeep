from __future__ import annotations

from services.strategies.strategy_registry import compute_signal


def _ohlcv(closes: list[float], *, volumes: list[float] | None = None) -> list[list[float]]:
    rows: list[list[float]] = []
    vols = list(volumes or [1.0 for _ in closes])
    prev = float(closes[0]) if closes else 0.0
    for idx, close in enumerate(closes):
        c = float(close)
        o = float(prev)
        h = max(o, c) + 0.2
        l = min(o, c) - 0.2
        rows.append([idx * 60_000, o, h, l, c, float(vols[idx])])
        prev = c
    return rows


def test_ema_cross_chop_filter_blocks_weak_cross():
    out = compute_signal(
        cfg={
            "strategy": {
                "name": "ema_cross",
                "ema_fast": 2,
                "ema_slow": 3,
                "filter_window": 6,
                "min_trend_efficiency": 0.50,
            }
        },
        symbol="BTC/USD",
        ohlcv=_ohlcv([100.0, 99.0, 100.0, 99.0, 100.0, 99.0, 100.5]),
    )

    assert out["action"] == "hold"
    assert out["reason"] == "chop_filter"


def test_mean_reversion_requires_reversal_confirmation():
    out = compute_signal(
        cfg={
            "strategy": {
                "name": "mean_reversion_rsi",
                "rsi_len": 3,
                "sma_len": 3,
                "rsi_buy": 35.0,
                "rsi_sell": 65.0,
                "filter_window": 5,
                "require_reversal_confirmation": True,
            }
        },
        symbol="BTC/USD",
        ohlcv=_ohlcv([100.0, 99.0, 98.0, 97.0, 96.0, 95.0, 94.0]),
    )

    assert out["action"] == "hold"
    assert out["reason"] == "reversal_not_confirmed"


def test_breakout_volume_filter_blocks_unconfirmed_breakout():
    out = compute_signal(
        cfg={
            "strategy": {
                "name": "breakout_donchian",
                "donchian_len": 3,
                "filter_window": 5,
                "min_volume_ratio": 1.20,
                "breakout_buffer_pct": 0.0,
                "require_directional_confirmation": True,
            }
        },
        symbol="BTC/USD",
        ohlcv=_ohlcv([100.0, 100.0, 100.0, 100.0, 100.0, 103.0], volumes=[2.0, 2.0, 2.0, 2.0, 2.0, 1.0]),
    )

    assert out["action"] == "hold"
    assert out["reason"] == "low_volume_filter"
