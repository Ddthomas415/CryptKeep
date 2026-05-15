from __future__ import annotations

from services.runtime.managed_symbol_config import normalize_symbols, resolve_managed_symbols


def test_resolve_managed_symbols_prefers_supervised_config(monkeypatch):
    monkeypatch.delenv("CBP_SYMBOLS", raising=False)

    out = resolve_managed_symbols(
        {
            "execution": {"symbols": ["btc/usd", "eth/usd"]},
            "pipeline": {"symbols": ["btc/usdc"]},
            "symbols": ["btc/usdt"],
        }
    )

    assert out == ["BTC/USD", "ETH/USD"]


def test_resolve_managed_symbols_prefers_env(monkeypatch):
    monkeypatch.setenv("CBP_SYMBOLS", "sol/usd, btc/usd")

    out = resolve_managed_symbols({"symbols": ["ETH/USD"]})

    assert out == ["SOL/USD", "BTC/USD"]


def test_normalize_symbols_dedupes_and_normalizes():
    assert normalize_symbols(["btc-usd", "BTC/USD", "eth/usd"]) == ["BTC/USD", "ETH/USD"]
