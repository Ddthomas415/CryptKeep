from __future__ import annotations

from typing import Any

from services.backtest import parity_engine
from services.backtest.parity_engine import run_parity_backtest
from services.strategies.composite_hybrid import STRATEGY_ID
from services.strategies.strategy_registry import SUPPORTED


def _candles(closes: list[float]) -> list[list[float]]:
    rows: list[list[float]] = []
    prev = float(closes[0]) if closes else 0.0
    for idx, close in enumerate(closes):
        c = float(close)
        o = float(prev)
        rows.append([idx * 60_000, o, max(o, c) + 0.1, min(o, c) - 0.1, c, 1.0])
        prev = c
    return rows


def _composite_cfg() -> dict[str, Any]:
    return {
        "strategy": {
            "name": STRATEGY_ID,
            "mode": "confirmation_gate",
            "primary": {"name": "breakout_donchian", "donchian_len": 3},
            "confirmer": {"name": "sma_200_trend", "sma_period": 3},
        }
    }


def test_run_parity_backtest_research_composite_confirmation_gate(monkeypatch) -> None:
    child_calls: list[str] = []

    def fake_compute_signal(*, cfg: dict[str, Any], symbol: str, ohlcv: list[list[Any]]) -> dict[str, Any]:
        name = str(cfg["strategy"]["name"])
        child_calls.append(name)
        step = len(ohlcv)
        if name == "breakout_donchian":
            if step == 3:
                return {"ok": True, "action": "buy", "reason": "primary_breakout", "confidence": 0.8}
            if step == 5:
                return {"ok": True, "action": "sell", "reason": "primary_exit", "confidence": 0.9}
        if name == "sma_200_trend":
            return {"ok": True, "action": "hold", "reason": "trend_ok", "direction": "bullish", "confidence": 0.7}
        return {"ok": True, "action": "hold", "reason": "unexpected_child"}

    monkeypatch.setattr(parity_engine, "compute_signal", fake_compute_signal)

    out = run_parity_backtest(
        cfg=_composite_cfg(),
        symbol="BTC/USDT",
        candles=_candles([100, 101, 102, 103, 104, 105]),
        warmup_bars=1,
        initial_cash=1_000.0,
        fee_bps=10.0,
        slippage_bps=5.0,
    )

    assert out["ok"] is True
    assert out["strategy"] == STRATEGY_ID
    assert out["buy_count"] == 1
    assert out["sell_count"] == 1
    assert out["trade_count"] == 2
    assert [trade["reason"] for trade in out["trades"]] == ["confirmation_gate_entry", "primary_exit"]
    assert all(trade["strategy"] == STRATEGY_ID for trade in out["trades"])
    assert child_calls.count("breakout_donchian") == 6
    assert child_calls.count("sma_200_trend") == 6
    assert STRATEGY_ID not in SUPPORTED


def test_run_parity_backtest_composite_translates_sma_flat_child_exit(monkeypatch) -> None:
    def fake_compute_signal(*, cfg: dict[str, Any], symbol: str, ohlcv: list[list[Any]]) -> dict[str, Any]:
        name = str(cfg["strategy"]["name"])
        step = len(ohlcv)
        if name == "breakout_donchian":
            if step == 2:
                return {"ok": True, "action": "buy", "reason": "primary_breakout", "confidence": 0.8}
            return {"ok": True, "action": "hold", "reason": "primary_hold"}
        if name == "sma_200_trend":
            if step >= 4:
                return {"ok": True, "action": "hold", "signal": "flat", "reason": "sma200:flat"}
            return {"ok": True, "action": "hold", "reason": "trend_ok", "direction": "bullish"}
        return {"ok": True, "action": "hold", "reason": "unexpected_child"}

    monkeypatch.setattr(parity_engine, "compute_signal", fake_compute_signal)

    out = run_parity_backtest(
        cfg=_composite_cfg(),
        symbol="BTC/USDT",
        candles=_candles([100, 101, 102, 101, 100]),
        warmup_bars=1,
        initial_cash=1_000.0,
        fee_bps=10.0,
        slippage_bps=5.0,
    )

    assert out["ok"] is True
    assert out["strategy"] == STRATEGY_ID
    assert out["buy_count"] == 1
    assert out["sell_count"] == 1
    assert out["trades"][-1]["reason"] == "confirmer_exit"
    assert out["metrics"]["closed_trades"] == 1
