from __future__ import annotations

from services.backtest.regimes import build_regime_scorecards, classify_market_regimes


def _candles(closes: list[float]) -> list[list[float]]:
    rows: list[list[float]] = []
    if not closes:
        return rows
    prev = float(closes[0])
    for i, close in enumerate(closes):
        c = float(close)
        o = float(prev)
        h = max(o, c) + 0.2
        l = min(o, c) - 0.2
        rows.append([i * 60_000, o, h, l, c, 1.0])
        prev = c
    return rows


def test_classify_market_regimes_detects_bull_and_bear_contexts():
    bull_rows = classify_market_regimes(
        _candles([100, 101, 102, 103, 104, 105, 106, 107]),
        trend_window=3,
        vol_window=3,
        low_vol_threshold=0.0001,
        high_vol_threshold=0.5,
        bull_threshold_pct=0.015,
        bear_threshold_pct=-0.015,
    )
    bear_rows = classify_market_regimes(
        _candles([107, 106, 105, 104, 103, 102, 101, 100]),
        trend_window=3,
        vol_window=3,
        low_vol_threshold=0.0001,
        high_vol_threshold=0.5,
        bull_threshold_pct=0.015,
        bear_threshold_pct=-0.015,
    )

    assert bull_rows[-1]["regime"] == "bull"
    assert bear_rows[-1]["regime"] == "bear"


def test_classify_market_regimes_detects_high_and_low_volatility():
    high_vol_rows = classify_market_regimes(
        _candles([100, 110, 95, 112, 92, 115, 90, 118]),
        trend_window=3,
        vol_window=3,
        low_vol_threshold=0.001,
        high_vol_threshold=0.05,
        bull_threshold_pct=0.2,
        bear_threshold_pct=-0.2,
    )
    low_vol_rows = classify_market_regimes(
        _candles([100, 100.1, 100.0, 100.1, 100.0, 100.1, 100.0, 100.1]),
        trend_window=3,
        vol_window=3,
        low_vol_threshold=0.002,
        high_vol_threshold=0.2,
        bull_threshold_pct=0.05,
        bear_threshold_pct=-0.05,
    )

    assert high_vol_rows[-1]["regime"] == "high_vol"
    assert low_vol_rows[-1]["regime"] == "low_vol"


def test_build_regime_scorecards_groups_rows_by_label():
    regime_rows = [
        {"ts_ms": 0, "regime": "bull"},
        {"ts_ms": 60_000, "regime": "bull"},
        {"ts_ms": 120_000, "regime": "bear"},
        {"ts_ms": 180_000, "regime": "bear"},
    ]
    equity = [
        {"ts_ms": 0, "equity": 1000.0, "pos_qty": 0.0},
        {"ts_ms": 60_000, "equity": 1010.0, "pos_qty": 1.0},
        {"ts_ms": 120_000, "equity": 990.0, "pos_qty": 1.0},
        {"ts_ms": 180_000, "equity": 995.0, "pos_qty": 0.0},
    ]
    trades = [
        {"ts_ms": 60_000, "action": "buy", "fee": 1.0},
        {"ts_ms": 180_000, "action": "sell", "fee": 1.0, "realized_pnl": -5.0},
    ]

    out = build_regime_scorecards(
        strategy="ema_cross",
        symbol="BTC/USD",
        trades=trades,
        equity=equity,
        regime_rows=regime_rows,
        fee_bps=10.0,
        slippage_bps=5.0,
    )

    assert out["bull"]["regime"] == "bull"
    assert out["bull"]["bars"] == 2
    assert out["bear"]["regime"] == "bear"
    assert out["bear"]["bars"] == 2
    assert out["bear"]["closed_trades"] == 1
