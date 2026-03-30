import os
import pytest

from services.execution.live_executor import _env_symbol, _env_venue


def test_env_symbol_requires_cbp_symbols(monkeypatch):
    monkeypatch.delenv("CBP_SYMBOLS", raising=False)
    with pytest.raises(RuntimeError, match="CBP_CONFIG_REQUIRED:missing_env:CBP_SYMBOLS"):
        _env_symbol()


def test_env_venue_requires_cbp_venue(monkeypatch):
    monkeypatch.delenv("CBP_VENUE", raising=False)
    with pytest.raises(RuntimeError, match="CBP_CONFIG_REQUIRED:missing_env:CBP_VENUE"):
        _env_venue()


def test_env_helpers_return_explicit_values(monkeypatch):
    monkeypatch.setenv("CBP_SYMBOLS", "ETH/USD,BTC/USD")
    monkeypatch.setenv("CBP_VENUE", "coinbase")
    assert _env_symbol() == "ETH/USD"
    assert _env_venue() == "coinbase"
