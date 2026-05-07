from __future__ import annotations

import pytest

from services.runtime.managed_symbol_config import resolve_managed_symbols


def test_resolve_managed_symbols_prefers_lane_lists_over_root_symbols(monkeypatch):
    monkeypatch.delenv("CBP_SYMBOLS", raising=False)

    cfg = {
        "symbols": ["BTC/USDT", "ETH/USDT"],
        "execution": {"symbols": ["btc/usd", "eth/usd"]},
        "pipeline": {"symbols": ["BTC/USD", "ETH/USD"]},
    }

    assert resolve_managed_symbols(cfg) == ["BTC/USD", "ETH/USD"]


def test_resolve_managed_symbols_prefers_env_override(monkeypatch):
    monkeypatch.setenv("CBP_SYMBOLS", "sol/usd,btc/usd")

    cfg = {
        "symbols": ["BTC/USDT", "ETH/USDT"],
        "execution": {"symbols": ["BTC/USD", "ETH/USD"]},
        "pipeline": {"symbols": ["BTC/USD", "ETH/USD"]},
    }

    assert resolve_managed_symbols(cfg) == ["SOL/USD", "BTC/USD"]


def test_resolve_managed_symbols_rejects_conflicting_lane_lists(monkeypatch):
    monkeypatch.delenv("CBP_SYMBOLS", raising=False)

    cfg = {
        "execution": {"symbols": ["BTC/USD"]},
        "pipeline": {"symbols": ["ETH/USD"]},
    }

    with pytest.raises(RuntimeError, match="execution.symbols_vs_pipeline.symbols"):
        resolve_managed_symbols(cfg)
