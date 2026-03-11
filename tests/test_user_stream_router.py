from __future__ import annotations

from services.fills import user_stream_router as usr


def test_ccxt_trade_to_fill_uses_exchange_id_when_trade_id_missing():
    trade = {
        "timestamp": 1_700_000_000_000,
        "order": "abc123",
        "symbol": "BTC/USD",
        "side": "buy",
        "amount": 0.01,
        "price": 100_000.0,
        "cost": 1_000.0,
        "fee": {"currency": "USD", "cost": 1.25},
    }
    f1 = usr.ccxt_trade_to_fill("coinbase", trade)
    f2 = usr.ccxt_trade_to_fill("coinbase", trade)
    assert f1["fill_id"].startswith("synthetic:")
    assert f1["fill_id"] == f2["fill_id"]
    assert f1["fee_usd"] == 1.25
    assert f1["venue"] == "coinbase"


def test_route_fill_event_prefers_live_executor_hook(monkeypatch):
    calls = {"hook": 0, "sink": 0}

    def _fake_hook(fill: dict, *, exec_db: str):
        calls["hook"] += 1
        return {"ok": True, "exec_db": exec_db, "fill_id": fill.get("fill_id")}

    class _Sink:
        def on_fill(self, _fill):
            calls["sink"] += 1

    monkeypatch.setattr(usr, "_resolve_live_executor_hook", lambda: _fake_hook)
    out = usr.route_fill_event(
        {"venue": "coinbase", "fill_id": "f-1", "symbol": "BTC/USD", "side": "buy", "qty": 1, "price": 100},
        exec_db=":memory:",
        prefer_live_executor_hook=True,
        fallback_sink=_Sink(),
    )
    assert out["ok"] is True
    assert out["via"] == "live_executor_hook"
    assert calls["hook"] == 1
    assert calls["sink"] == 0


def test_route_fill_event_falls_back_to_fill_sink_when_hook_missing(monkeypatch):
    calls = {"sink": 0}

    class _Sink:
        def on_fill(self, _fill):
            calls["sink"] += 1

    monkeypatch.setattr(usr, "_resolve_live_executor_hook", lambda: None)
    out = usr.route_fill_event(
        {"venue": "coinbase", "fill_id": "f-2", "symbol": "BTC/USD", "side": "sell", "qty": 1, "price": 100},
        exec_db=":memory:",
        prefer_live_executor_hook=True,
        fallback_sink=_Sink(),
    )
    assert out["ok"] is True
    assert out["via"] == "fill_sink"
    assert calls["sink"] == 1


def test_route_ccxt_trade_rejects_invalid_shape():
    out = usr.route_ccxt_trade(
        "coinbase",
        {"id": "x-1", "side": "buy", "amount": None, "price": None},
        exec_db=":memory:",
        prefer_live_executor_hook=False,
    )
    assert out["ok"] is False
    assert out["reason"] == "invalid_trade_shape"

