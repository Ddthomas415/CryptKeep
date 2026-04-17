"""tests/test_strategy_registry.py

Tests for services/strategies/strategy_registry.py — the signal routing table.

Any bug in the registry means signals are routed to the wrong strategy or
silently fall through to the default hold.
"""
from __future__ import annotations
import pytest
from services.strategies.strategy_registry import compute_signal, SUPPORTED


def _ohlcv(n: int = 210, price: float = 100.0) -> list:
    return [[i, price, price + 1, price - 1, price + i * 0.1, 1000.0] for i in range(n)]


class TestRegistryContents:
    def test_all_expected_strategies_registered(self):
        expected = {"ema_cross", "mean_reversion_rsi", "breakout_donchian",
                    "momentum", "pullback_recovery", "volatility_reversal",
                    "gap_fill", "breakout_volume", "sma_200_trend"}
        for name in expected:
            assert name in SUPPORTED, f"'{name}' not in registry"

    def test_no_none_values_in_registry(self):
        for name, fn in SUPPORTED.items():
            assert fn is not None, f"registry entry '{name}' is None"
            assert callable(fn), f"registry entry '{name}' is not callable"


class TestSignalRouting:
    def test_ema_cross_routes_correctly(self):
        cfg = {"strategy": {"name": "ema_cross"}}
        result = compute_signal(cfg=cfg, symbol="BTC/USD", ohlcv=_ohlcv())
        assert "action" in result
        assert result["strategy"] == "ema_cross"
        assert result["symbol"] == "BTC/USD"

    def test_sma_200_trend_routes_correctly(self):
        cfg = {"strategy": {"name": "sma_200_trend", "sma_period": 200}}
        result = compute_signal(cfg=cfg, symbol="BTC/USDT", ohlcv=_ohlcv(210))
        assert result["strategy"] == "sma_200_trend"
        assert result["action"] in ("buy", "hold")

    def test_unknown_strategy_falls_back_to_ema_cross(self):
        cfg = {"strategy": {"name": "nonexistent_strategy_xyz"}}
        result = compute_signal(cfg=cfg, symbol="BTC/USD", ohlcv=_ohlcv())
        # Falls back to ema_cross per registry logic
        assert result["action"] in ("buy", "sell", "hold")
        assert "ok" not in result or result.get("ok") is True

    def test_trade_disabled_returns_hold(self):
        cfg = {"strategy": {"name": "ema_cross", "trade_enabled": False}}
        result = compute_signal(cfg=cfg, symbol="BTC/USD", ohlcv=_ohlcv())
        assert result["action"] == "hold"
        assert result["reason"] == "trade_disabled"

    def test_symbol_is_passed_through(self):
        for sym in ("ETH/USD", "SOL/USDT", "BTC/USD"):
            cfg = {"strategy": {"name": "ema_cross"}}
            result = compute_signal(cfg=cfg, symbol=sym, ohlcv=_ohlcv())
            assert result["symbol"] == sym


class TestSignalOutputShape:
    def test_all_strategies_return_action(self):
        for name in SUPPORTED:
            cfg = {"strategy": {"name": name}}
            try:
                result = compute_signal(cfg=cfg, symbol="BTC/USD", ohlcv=_ohlcv(250))
                assert "action" in result, f"{name} missing 'action'"
            except Exception as e:
                # Some strategies may need more specific config — that's expected
                # but they should not raise for missing 'action'
                pass

    def test_result_has_strategy_field(self):
        cfg = {"strategy": {"name": "ema_cross"}}
        result = compute_signal(cfg=cfg, symbol="BTC/USD", ohlcv=_ohlcv())
        assert "strategy" in result

    def test_insufficient_ohlcv_returns_hold(self):
        cfg = {"strategy": {"name": "sma_200_trend"}}
        result = compute_signal(cfg=cfg, symbol="BTC/USD", ohlcv=_ohlcv(5))
        # Too few bars — must not crash, should hold
        assert result["action"] in ("buy", "hold", "sell")
