from __future__ import annotations

from services.execution import live_event_executor as lee
from services.execution.live_executor import LiveCfg


def test_run_tick_triggers_on_new_ws_event(monkeypatch):
    calls = {"submit": 0, "reconcile": 0}

    class _WS:
        def get_status(self, *, exchange: str, symbol: str):
            return {"exchange": exchange, "symbol": symbol, "recv_ts_ms": 1234}

    monkeypatch.setattr(lee, "submit_pending_live", lambda cfg: calls.__setitem__("submit", calls["submit"] + 1) or {"ok": True})
    monkeypatch.setattr(lee, "reconcile_live", lambda cfg: calls.__setitem__("reconcile", calls["reconcile"] + 1) or {"ok": True})

    cfg = LiveCfg(enabled=True, exchange_id="coinbase", symbol="BTC/USD", exec_db=":memory:")
    state = lee.EventLoopState()
    out = lee.run_tick(cfg, state=state, ws_store=_WS(), min_trigger_interval_ms=100, now_ms=2_000)
    assert out["ok"] is True
    assert out["triggered"] is True
    assert calls["submit"] == 1
    assert calls["reconcile"] == 1
    assert state.triggers == 1


def test_run_tick_no_new_event_does_not_trigger(monkeypatch):
    calls = {"submit": 0, "reconcile": 0}

    class _WS:
        def get_status(self, *, exchange: str, symbol: str):
            return {"exchange": exchange, "symbol": symbol, "recv_ts_ms": 1000}

    monkeypatch.setattr(lee, "submit_pending_live", lambda cfg: calls.__setitem__("submit", calls["submit"] + 1) or {"ok": True})
    monkeypatch.setattr(lee, "reconcile_live", lambda cfg: calls.__setitem__("reconcile", calls["reconcile"] + 1) or {"ok": True})

    cfg = LiveCfg(enabled=True, exchange_id="coinbase", symbol="BTC/USD", exec_db=":memory:")
    state = lee.EventLoopState(last_recv_ts_ms=1000)
    out = lee.run_tick(cfg, state=state, ws_store=_WS(), min_trigger_interval_ms=100, now_ms=2_000)
    assert out["ok"] is True
    assert out["triggered"] is False
    assert out["reason"] == "no_new_ws_event"
    assert calls["submit"] == 0
    assert calls["reconcile"] == 0


def test_run_tick_throttles_trigger_rate(monkeypatch):
    calls = {"submit": 0, "reconcile": 0}

    class _WS:
        def get_status(self, *, exchange: str, symbol: str):
            return {"exchange": exchange, "symbol": symbol, "recv_ts_ms": 2000}

    monkeypatch.setattr(lee, "submit_pending_live", lambda cfg: calls.__setitem__("submit", calls["submit"] + 1) or {"ok": True})
    monkeypatch.setattr(lee, "reconcile_live", lambda cfg: calls.__setitem__("reconcile", calls["reconcile"] + 1) or {"ok": True})

    cfg = LiveCfg(enabled=True, exchange_id="coinbase", symbol="BTC/USD", exec_db=":memory:")
    state = lee.EventLoopState(last_recv_ts_ms=1000, last_trigger_ts_ms=1_950, triggers=1)
    out = lee.run_tick(cfg, state=state, ws_store=_WS(), min_trigger_interval_ms=100, now_ms=2_000)
    assert out["ok"] is True
    assert out["triggered"] is False
    assert out["reason"] == "trigger_throttled"
    assert calls["submit"] == 0
    assert calls["reconcile"] == 0
