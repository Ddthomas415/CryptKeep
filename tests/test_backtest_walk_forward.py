from __future__ import annotations

from services.backtest.walk_forward import run_anchored_walk_forward


def _candles(closes: list[float]) -> list[list[float]]:
    rows: list[list[float]] = []
    if not closes:
        return rows
    prev = float(closes[0])
    for i, close in enumerate(closes):
        cur = float(close)
        open_px = float(prev)
        rows.append([i * 60_000, open_px, max(open_px, cur) + 0.2, min(open_px, cur) - 0.2, cur, 1.0])
        prev = cur
    return rows


def test_run_anchored_walk_forward_returns_research_only_window_summary() -> None:
    prices = [
        100, 99, 98, 97, 96, 95, 94, 93, 92, 91,
        90, 91, 92, 93, 94, 95, 96, 97, 98, 99,
        100, 101, 102, 103, 104, 105, 104, 103, 102, 101,
        100, 99, 98, 97, 96, 95, 94, 95, 96, 97,
        98, 99, 100, 101, 102, 103, 102, 101, 100, 99,
    ]
    out = run_anchored_walk_forward(
        cfg={"strategy": {"name": "ema_cross", "ema_fast": 3, "ema_slow": 5}},
        symbol="BTC/USD",
        candles=_candles(prices),
        warmup_bars=5,
        min_train_bars=20,
        test_bars=10,
        step_bars=10,
        initial_cash=1_000.0,
        fee_bps=10.0,
        slippage_bps=5.0,
    )

    assert out["ok"] is True
    assert out["research_only"] is True
    assert out["strategy"] == "ema_cross"
    assert out["window_count"] == 3
    assert out["summary"]["window_count"] == 3
    assert out["summary"]["total_test_trades"] >= 0
    assert 0.0 <= float(out["summary"]["non_negative_test_window_ratio"]) <= 1.0

    first = out["windows"][0]
    assert first["window_index"] == 1
    assert first["train_bars"] == 20
    assert first["test_bars"] == 10
    assert first["train_start_ts_ms"] == 0
    assert first["test_start_ts_ms"] == 20 * 60_000
    assert "total_return_pct" in first["train_metrics"]
    assert "test_return_pct" in first["test_metrics"]
    assert "max_drawdown_pct" in first["test_metrics"]


def test_run_anchored_walk_forward_returns_insufficient_candles_without_windows() -> None:
    out = run_anchored_walk_forward(
        cfg={"strategy": {"name": "breakout_donchian", "donchian_len": 5}},
        symbol="BTC/USD",
        candles=_candles([100, 101, 102, 103, 104, 105]),
        warmup_bars=5,
        min_train_bars=20,
        test_bars=10,
    )

    assert out["ok"] is False
    assert out["reason"] == "insufficient_candles"
    assert out["research_only"] is True
    assert out["window_count"] == 0
    assert out["windows"] == []


def test_run_anchored_walk_forward_keeps_train_anchor_fixed_and_steps_forward() -> None:
    prices = [100.0 + (0.5 * i) for i in range(60)]
    out = run_anchored_walk_forward(
        cfg={"strategy": {"name": "breakout_donchian", "donchian_len": 5}},
        symbol="BTC/USD",
        candles=_candles(prices),
        warmup_bars=5,
        min_train_bars=24,
        test_bars=8,
        step_bars=6,
        max_windows=3,
    )

    assert out["ok"] is True
    assert out["window_count"] == 3
    assert [row["train_bars"] for row in out["windows"]] == [24, 30, 36]
    assert [row["test_bars"] for row in out["windows"]] == [8, 8, 8]
    assert [row["train_start_ts_ms"] for row in out["windows"]] == [0, 0, 0]
