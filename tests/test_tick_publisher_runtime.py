from __future__ import annotations

from scripts import run_tick_publisher as tick_wrapper
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


def test_fetch_status_uses_sample_ohlcv_ticks_when_enabled(monkeypatch) -> None:
    monkeypatch.setenv("CBP_USE_SAMPLE_OHLCV", "1")
    monkeypatch.setenv("CBP_VENUE", "coinbase")
    monkeypatch.setenv("CBP_SYMBOLS", "BTC/USDT")
    monkeypatch.setattr(system_status_publisher.time, "time", lambda: 123.456)
    monkeypatch.setattr(
        system_status_publisher,
        "_sample_tick",
        lambda symbol, timeframe="1d": {
            "symbol": str(symbol),
            "ts_ms": 111111,
            "bid": 44800.0,
            "ask": 44800.0,
            "last": 44800.0,
        },
    )
    monkeypatch.setattr(
        system_status_publisher,
        "make_exchange",
        lambda venue, creds, enable_rate_limit=True: (_ for _ in ()).throw(AssertionError("exchange should not be called in sample mode")),
    )

    out = system_status_publisher.fetch_status()

    assert out["venues"]["coinbase"]["ok"] is True
    assert out["venues"]["coinbase"]["last"] == 44800.0
    assert out["ticks"] == [
        {
            "venue": "coinbase",
            "symbol": "BTC/USDT",
            "symbol_mapped": "BTC/USDT",
            "bid": 44800.0,
            "ask": 44800.0,
            "last": 44800.0,
            "ts_ms": 123456,
            "exchange_ts_ms": 111111,
        }
    ]


def test_run_forever_creates_snapshot_dir_before_write(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(system_status_publisher, "FLAGS", tmp_path / "flags")
    monkeypatch.setattr(system_status_publisher, "LOCKS", tmp_path / "locks")
    monkeypatch.setattr(system_status_publisher, "SNAPSHOTS", tmp_path / "snapshots")
    monkeypatch.setattr(system_status_publisher, "STOP_FILE", (tmp_path / "flags" / "tick_publisher.stop"))
    monkeypatch.setattr(system_status_publisher, "LOCK_FILE", (tmp_path / "locks" / "tick_publisher.lock"))
    monkeypatch.setattr(system_status_publisher, "STATUS_FILE", (tmp_path / "snapshots" / "system_status.latest.json"))
    monkeypatch.setattr(system_status_publisher, "ensure_dirs", lambda: None)
    monkeypatch.setattr(system_status_publisher, "_acquire_lock", lambda: True)
    monkeypatch.setattr(system_status_publisher, "_release_lock", lambda: None)
    monkeypatch.setattr(
        system_status_publisher,
        "fetch_status",
        lambda: {"ts": "2026-01-01T00:00:00Z", "ts_ms": 1, "venues": {}, "ticks": []},
    )

    def _sleep(_seconds: float) -> None:
        system_status_publisher.STOP_FILE.parent.mkdir(parents=True, exist_ok=True)
        system_status_publisher.STOP_FILE.write_text("stop\n", encoding="utf-8")

    monkeypatch.setattr(system_status_publisher.time, "sleep", _sleep)

    system_status_publisher.run_forever()

    assert system_status_publisher.STATUS_FILE.exists() is True
    payload = system_status_publisher.STATUS_FILE.read_text(encoding="utf-8")
    assert '"ticks": []' in payload


def test_tick_wrapper_accepts_runtime_only_config_for_prereqs(monkeypatch, tmp_path) -> None:
    logs: list[str] = []

    monkeypatch.setattr(tick_wrapper, "_REPO", tmp_path)
    monkeypatch.setattr(tick_wrapper, "runtime_trading_config_available", lambda: True)
    monkeypatch.setattr(tick_wrapper, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(tick_wrapper, "log", logs.append)
    (tmp_path / "execution.sqlite").write_text("", encoding="utf-8")
    monkeypatch.setattr(system_status_publisher, "run_tick_publisher", lambda: None)

    out = tick_wrapper.main()

    assert out == 0
    assert logs[0] == "tick_publisher starting (prereqs present)"


def test_tick_wrapper_reports_missing_runtime_config(monkeypatch, tmp_path) -> None:
    logs: list[str] = []

    monkeypatch.setattr(tick_wrapper, "_REPO", tmp_path)
    monkeypatch.setattr(tick_wrapper, "runtime_trading_config_available", lambda: False)
    monkeypatch.setattr(tick_wrapper, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(tick_wrapper, "log", logs.append)
    monkeypatch.setattr(system_status_publisher, "run_tick_publisher", lambda: None)

    out = tick_wrapper.main()

    assert out == 0
    assert logs[0].startswith("tick_publisher starting in IDLE mode:")
    assert "runtime trading config missing" in logs[0]
