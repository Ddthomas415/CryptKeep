from __future__ import annotations

import json

from scripts import run_ws_ticker_feed as mod


def test_default_values_prefer_env_over_runtime_config(monkeypatch):
    monkeypatch.setenv("CBP_VENUE", "coinbase_adv")
    monkeypatch.setenv("CBP_SYMBOLS", "ETH/USD,BTC/USD")
    monkeypatch.setattr(mod, "runtime_trading_config_available", lambda: True)
    monkeypatch.setattr(
        mod,
        "load_runtime_trading_config",
        lambda: {"live": {"exchange_id": "binance"}, "symbols": ["SOL/USDT"]},
    )

    assert mod._default_venue() == "coinbase"
    assert mod._default_symbol() == "ETH/USD"


def test_default_values_fall_back_to_runtime_config(monkeypatch):
    monkeypatch.delenv("CBP_VENUE", raising=False)
    monkeypatch.delenv("CBP_SYMBOLS", raising=False)
    monkeypatch.setattr(mod, "runtime_trading_config_available", lambda: True)
    monkeypatch.setattr(
        mod,
        "load_runtime_trading_config",
        lambda: {
            "live": {"exchange_id": "binance"},
            "pipeline": {"exchange_id": "coinbase"},
            "symbols": ["BTC/USDT"],
        },
    )

    assert mod._default_venue() == "binance"
    assert mod._default_symbol() == "BTC/USDT"


def test_request_stop_writes_stop_flag(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "FLAGS", tmp_path)
    monkeypatch.setattr(mod, "STOP_FILE", tmp_path / "market_ws.stop")
    monkeypatch.setattr(mod, "ensure_dirs", lambda: None)

    out = mod.request_stop()

    assert out["ok"] is True
    assert json.loads(json.dumps(out))["stop_file"].endswith("market_ws.stop")
    assert (tmp_path / "market_ws.stop").exists()


def test_exchange_init_failure_writes_market_ws_status(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "HEALTH", tmp_path)
    monkeypatch.setattr(mod, "STATUS_FILE", tmp_path / "market_ws.json")
    monkeypatch.setattr(mod, "STOP_FILE", tmp_path / "market_ws.stop")
    monkeypatch.setattr(mod, "ensure_dirs", lambda: None)
    monkeypatch.setattr(mod, "_build_exchange", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")))

    assert mod.main(["run"]) == 2

    payload = json.loads((tmp_path / "market_ws.json").read_text(encoding="utf-8"))
    assert payload["status"] == "error"
    assert payload["reason"] == "exchange_init_failed"
    assert payload["events"] == 0


def test_max_events_writes_market_ws_status(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "HEALTH", tmp_path)
    monkeypatch.setattr(mod, "STATUS_FILE", tmp_path / "market_ws.json")
    monkeypatch.setattr(mod, "STOP_FILE", tmp_path / "market_ws.stop")
    monkeypatch.setattr(mod, "ensure_dirs", lambda: None)
    monkeypatch.setattr(mod, "_build_exchange", lambda *_args, **_kwargs: object())

    class _DummyFeed:
        def __init__(self, *, exchange, venue, symbol, cfg):
            self.exchange = exchange
            self.venue = venue
            self.symbol = symbol
            self.cfg = cfg

        async def stream(self, *, stop_event=None):
            yield {"symbol": "BTC/USD", "ts_ms": 1234}

    monkeypatch.setattr(mod, "WSTickerFeed", _DummyFeed)

    assert mod.main(["run", "--max-events", "1"]) == 0

    payload = json.loads((tmp_path / "market_ws.json").read_text(encoding="utf-8"))
    assert payload["status"] == "stopped"
    assert payload["reason"] == "max_events"
    assert payload["events"] == 1
    assert payload["symbol"] == "BTC/USD"
