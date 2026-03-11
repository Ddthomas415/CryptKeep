from unittest.mock import patch

import pytest

from services.execution import strategy_runner


class DummyException(Exception):
    pass


def test_runner_iteration_emits_heartbeat(monkeypatch):
    events = []

    def fake_log_event(venue, symbol, event, **kwargs):
        events.append((event, kwargs.get("payload")))

    monkeypatch.setattr(strategy_runner, "log_event", fake_log_event)
    monkeypatch.setattr(strategy_runner, "run_once", lambda: None)

    strategy_runner._runner_iteration()

    assert events and events[-1][0] == "strategy_heartbeat"
    payload = events[-1][1]
    assert isinstance(payload, dict)
    assert "timestamp" in payload


def test_runner_iteration_logs_error(monkeypatch):
    events = []

    def fake_log_event(venue, symbol, event, **kwargs):
        events.append((event, kwargs.get("payload")))

    def raise_error():
        raise DummyException("boom")

    monkeypatch.setattr(strategy_runner, "log_event", fake_log_event)
    monkeypatch.setattr(strategy_runner, "run_once", raise_error)

    with pytest.raises(DummyException):
        strategy_runner._runner_iteration()

    assert any(event == "strategy_error" for event, _ in events)

def test_env_symbol_uses_first_symbol_from_csv(monkeypatch):
    monkeypatch.setenv("CBP_SYMBOLS", "ETH/USD, BTC/USD , SOL/USD")
    monkeypatch.delenv("SYMBOLS", raising=False)

    assert strategy_runner._env_symbol() == "ETH/USD"


def test_env_symbol_falls_back_to_symbols_env(monkeypatch):
    monkeypatch.delenv("CBP_SYMBOLS", raising=False)
    monkeypatch.setenv("SYMBOLS", "LTC/USD, BTC/USD")

    assert strategy_runner._env_symbol() == "LTC/USD"


def test_env_symbol_returns_default_when_empty(monkeypatch):
    monkeypatch.delenv("CBP_SYMBOLS", raising=False)
    monkeypatch.delenv("SYMBOLS", raising=False)

    assert strategy_runner._env_symbol() == "BTC/USD"


def test_env_venue_prefers_cbp_venue(monkeypatch):
    monkeypatch.setenv("CBP_VENUE", "kraken")
    monkeypatch.setenv("EXCHANGE_ID", "coinbase")

    assert strategy_runner._env_venue() == "kraken"

