import os

import pytest

from services.strategy.startup_guard import StartupGuardError, require_known_flat_or_override


class DummyStore:
    def __init__(self, row):
        self._row = row
    def get(self, venue: str, symbol: str):
        return self._row


def test_unknown_state_halts(monkeypatch):
    monkeypatch.setattr("services.strategy.startup_guard.PositionStateSQLite", lambda: DummyStore(None))
    monkeypatch.delenv("CBP_STARTUP_CONFIRM_FLAT", raising=False)
    with pytest.raises(StartupGuardError, match="unknown_position_state"):
        require_known_flat_or_override(venue="binance", symbol="BTC/USDT")


def test_confirm_flat_allows_unknown(monkeypatch):
    monkeypatch.setattr("services.strategy.startup_guard.PositionStateSQLite", lambda: DummyStore(None))
    monkeypatch.setenv("CBP_STARTUP_CONFIRM_FLAT", "true")
    require_known_flat_or_override(venue="binance", symbol="BTC/USDT")


def test_open_position_halts_without_override(monkeypatch):
    monkeypatch.setattr("services.strategy.startup_guard.PositionStateSQLite", lambda: DummyStore({"qty": 1.0}))
    monkeypatch.delenv("CBP_STARTUP_ALLOW_OPEN_POSITION", raising=False)
    with pytest.raises(StartupGuardError, match="open_position_requires_override"):
        require_known_flat_or_override(venue="binance", symbol="BTC/USDT")


def test_open_position_allows_with_override(monkeypatch):
    monkeypatch.setattr("services.strategy.startup_guard.PositionStateSQLite", lambda: DummyStore({"qty": 1.0}))
    monkeypatch.setenv("CBP_STARTUP_ALLOW_OPEN_POSITION", "true")
    require_known_flat_or_override(venue="binance", symbol="BTC/USDT")
