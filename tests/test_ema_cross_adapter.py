from __future__ import annotations

from services.strategies.ema_cross import signal_from_ohlcv


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


def test_signal_from_ohlcv_returns_mapping_for_insufficient_history() -> None:
    out = signal_from_ohlcv(_ohlcv([100.0, 101.0, 102.0]), ema_fast=3, ema_slow=5)

    assert out["ok"] is False
    assert out["action"] == "hold"
    assert out["reason"] in {"insufficient_ohlcv", "insufficient_history"}


def test_signal_from_ohlcv_returns_mapping_for_valid_ema_cross() -> None:
    out = signal_from_ohlcv(
        _ohlcv([10.0, 9.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0]),
        ema_fast=2,
        ema_slow=4,
    )

    assert out["ok"] is True
    assert out["action"] in {"buy", "sell", "hold"}
    assert "ind" in out


def test_signal_from_ohlcv_applies_chop_filter() -> None:
    out = signal_from_ohlcv(
        _ohlcv([100.0, 99.0, 100.0, 99.0, 100.0, 99.0, 100.5]),
        ema_fast=2,
        ema_slow=3,
        filter_window=6,
        min_trend_efficiency=0.50,
    )

    assert out["ok"] is True
    assert out["action"] == "hold"
    assert out["reason"] == "chop_filter"
