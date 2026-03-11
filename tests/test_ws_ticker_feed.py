from __future__ import annotations

import asyncio

from services.marketdata import ws_ticker_feed as wtf


class _ExchangeNoWatch:
    has = {"watchTicker": False}


class _ExchangeErrThenOk:
    has = {"watchTicker": True}

    def __init__(self):
        self.calls = 0

    async def watch_ticker(self, _symbol: str):
        self.calls += 1
        if self.calls <= 2:
            raise RuntimeError("boom")
        return {"symbol": "BTC/USD", "bid": 100.0, "ask": 101.0, "last": 100.5, "timestamp": 1234}


def test_next_ticker_disables_when_unsupported(monkeypatch):
    disabled_calls: list[dict] = []
    monkeypatch.setattr(wtf.blacklist, "is_disabled", lambda **kwargs: {"ok": True, "disabled": False})
    monkeypatch.setattr(wtf.blacklist, "disable", lambda **kwargs: disabled_calls.append(kwargs) or {"ok": True, "key": "k"})
    feed = wtf.WSTickerFeed(exchange=_ExchangeNoWatch(), venue="coinbase", symbol="BTC/USD")
    out = asyncio.run(feed.next_ticker())
    assert out["ok"] is False
    assert out["reason"] == "unsupported_watchTicker"
    assert disabled_calls and disabled_calls[0]["feature"] == "watchTicker"


def test_next_ticker_error_threshold_auto_disables(monkeypatch):
    ex = _ExchangeErrThenOk()
    disabled_calls: list[dict] = []
    monkeypatch.setattr(wtf.blacklist, "is_disabled", lambda **kwargs: {"ok": True, "disabled": False})
    monkeypatch.setattr(wtf.blacklist, "disable", lambda **kwargs: disabled_calls.append(kwargs) or {"ok": True, "key": "k"})
    feed = wtf.WSTickerFeed(
        exchange=ex,
        venue="coinbase",
        symbol="BTC/USD",
        cfg=wtf.WSTickerFeedCfg(max_errors_before_disable=2, disable_cooldown_sec=60),
    )
    a = asyncio.run(feed.next_ticker())
    b = asyncio.run(feed.next_ticker())
    assert a["ok"] is False and b["ok"] is False
    assert bool(b.get("disabled")) is True
    assert disabled_calls and "boom" in str(disabled_calls[-1]["reason"])


def test_next_ticker_success_resets_errors_and_normalizes(monkeypatch):
    ex = _ExchangeErrThenOk()
    monkeypatch.setattr(wtf.blacklist, "is_disabled", lambda **kwargs: {"ok": True, "disabled": False})
    monkeypatch.setattr(wtf.blacklist, "disable", lambda **kwargs: {"ok": True, "key": "k"})
    feed = wtf.WSTickerFeed(
        exchange=ex,
        venue="coinbase",
        symbol="BTC/USD",
        cfg=wtf.WSTickerFeedCfg(max_errors_before_disable=99, disable_cooldown_sec=60),
    )
    asyncio.run(feed.next_ticker())
    asyncio.run(feed.next_ticker())
    out = asyncio.run(feed.next_ticker())
    assert out["ok"] is True
    q = out["quote"]
    assert q["venue"] == "coinbase"
    assert q["symbol"] == "BTC/USD"
    assert q["bid"] == 100.0
    assert q["ask"] == 101.0
    assert feed._errors == 0

