from __future__ import annotations

from services.market_data import system_status_publisher


def test_tick_publisher_poll_interval_defaults_to_two_seconds(monkeypatch) -> None:
    monkeypatch.delenv("CBP_TICK_PUBLISH_INTERVAL_SEC", raising=False)

    assert system_status_publisher._poll_interval_sec() == 2.0


def test_tick_publisher_poll_interval_honors_env_override(monkeypatch) -> None:
    monkeypatch.setenv("CBP_TICK_PUBLISH_INTERVAL_SEC", "1.5")

    assert system_status_publisher._poll_interval_sec() == 1.5


def test_tick_publisher_poll_interval_invalid_env_falls_back(monkeypatch) -> None:
    monkeypatch.setenv("CBP_TICK_PUBLISH_INTERVAL_SEC", "not-a-number")

    assert system_status_publisher._poll_interval_sec() == 2.0


def test_tick_publisher_symbol_defaults_to_btc_usd(monkeypatch) -> None:
    monkeypatch.delenv("CBP_SYMBOLS", raising=False)

    assert system_status_publisher._symbol() == "BTC/USD"


def test_tick_publisher_symbol_uses_first_env_symbol(monkeypatch) -> None:
    monkeypatch.setenv("CBP_SYMBOLS", "ETH/USD,BTC/USD")

    assert system_status_publisher._symbol() == "ETH/USD"
