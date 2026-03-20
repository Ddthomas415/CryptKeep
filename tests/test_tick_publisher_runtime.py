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


def test_fetch_status_includes_symbol_specific_ticks(monkeypatch) -> None:
    class _FakeExchange:
        id = "coinbase"

        def fetch_ticker(self, symbol):
            assert symbol == "SUI/USD"
            return {"bid": 1.0, "ask": 1.2, "last": 1.1, "timestamp": 111111}

        def close(self):
            return None

    monkeypatch.setenv("CBP_VENUE", "coinbase")
    monkeypatch.setenv("CBP_SYMBOLS", "SUI/USD")
    monkeypatch.setattr(system_status_publisher.time, "time", lambda: 123.456)
    monkeypatch.setattr(system_status_publisher, "make_exchange", lambda venue, creds, enable_rate_limit=True: _FakeExchange())
    monkeypatch.setattr(system_status_publisher, "map_symbol", lambda venue, symbol: symbol)

    out = system_status_publisher.fetch_status()

    assert out["venues"]["coinbase"]["ok"] is True
    assert out["venues"]["coinbase"]["timestamp"] == 123456
    assert out["venues"]["coinbase"]["exchange_timestamp"] == 111111
    assert out["ticks"] == [
        {
            "venue": "coinbase",
            "symbol": "SUI/USD",
            "symbol_mapped": "SUI/USD",
            "bid": 1.0,
            "ask": 1.2,
            "last": 1.1,
            "ts_ms": 123456,
            "exchange_ts_ms": 111111,
        }
    ]
