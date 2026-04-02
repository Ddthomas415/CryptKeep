import pytest

import ccxt  # type: ignore

from services.execution.adapters.factory import get_adapter
from services.security.exchange_factory import (
    VenueResolutionError,
    make_exchange,
)


class _DummyExchange:
    def __init__(self, cfg):
        self.cfg = dict(cfg or {})
        self.sandbox = False

    def set_sandbox_mode(self, value):
        self.sandbox = bool(value)


def test_make_exchange_uses_explicit_venue_when_env_missing(monkeypatch):
    monkeypatch.delenv("CBP_VENUE", raising=False)
    monkeypatch.setattr(ccxt, "coinbase", _DummyExchange, raising=False)

    ex = make_exchange("coinbase", {"apiKey": "k", "secret": "s"})

    assert isinstance(ex, _DummyExchange)
    assert ex.cfg["apiKey"] == "k"
    assert ex.cfg["secret"] == "s"


def test_make_exchange_rejects_env_conflict(monkeypatch):
    monkeypatch.setenv("CBP_VENUE", "coinbase")

    with pytest.raises(VenueResolutionError, match="CBP_VENUE conflict"):
        make_exchange("kraken", {"apiKey": "k", "secret": "s"})


def test_make_exchange_rejects_missing_venue(monkeypatch):
    monkeypatch.delenv("CBP_VENUE", raising=False)

    with pytest.raises(VenueResolutionError, match="venue is required"):
        make_exchange("", {"apiKey": "k", "secret": "s"})


def test_get_adapter_accepts_matching_env_and_explicit(monkeypatch):
    monkeypatch.setenv("CBP_VENUE", "coinbase")
    monkeypatch.setattr(ccxt, "coinbase", _DummyExchange, raising=False)

    ex = get_adapter("coinbase", sandbox=True)

    assert isinstance(ex, _DummyExchange)
    assert ex.sandbox is True


def test_get_adapter_rejects_env_conflict(monkeypatch):
    monkeypatch.setenv("CBP_VENUE", "coinbase")

    with pytest.raises(VenueResolutionError, match="CBP_VENUE conflict"):
        get_adapter("kraken")


def test_get_adapter_rejects_missing_venue(monkeypatch):
    monkeypatch.delenv("CBP_VENUE", raising=False)

    with pytest.raises(VenueResolutionError, match="venue is required"):
        get_adapter("")
