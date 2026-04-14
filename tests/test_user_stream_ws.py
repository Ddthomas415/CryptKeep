from __future__ import annotations
import pytest

import asyncio

import services.fills.user_stream_ws as usws


class _FakeWSClient:
    def __init__(self):
        self.calls = 0
        self.closed = False

    async def watch_my_trades(self, _symbol=None):
        self.calls += 1
        if self.calls == 1:
            return [
                {
                    "id": "t-1",
                    "timestamp": 1_700_000_000_000,
                    "symbol": "BTC/USD",
                    "side": "buy",
                    "amount": 0.01,
                    "price": 100_000.0,
                }
            ]
        return []

    def close(self):
        self.closed = True


@pytest.mark.slow
def test_user_stream_run_once_routes_trades(monkeypatch, tmp_path):
    cfg = usws.UserStreamWSConfig(exchange_id="coinbase", exec_db=str(tmp_path / "exec.sqlite"), symbol="BTC/USD")
    svc = usws.UserStreamFillService(cfg)
    fake = _FakeWSClient()
    monkeypatch.setattr(svc, "_build_ws_client", lambda: fake)

    routed: list[tuple[str, dict, dict]] = []

    def _fake_route(exchange_id: str, trade: dict, **kwargs):
        routed.append((exchange_id, trade, kwargs))
        return {"ok": True}

    monkeypatch.setattr(usws, "route_ccxt_trade", _fake_route)
    out = asyncio.run(svc.run_once())
    assert out["ok"] is True
    assert out["processed"] == 1
    assert routed and routed[0][0] == "coinbase"
    assert routed[0][2]["exec_db"] == str(tmp_path / "exec.sqlite")


@pytest.mark.slow
def test_user_stream_run_once_handles_missing_client(monkeypatch, tmp_path):
    cfg = usws.UserStreamWSConfig(exchange_id="coinbase", exec_db=str(tmp_path / "exec.sqlite"))
    svc = usws.UserStreamFillService(cfg)
    monkeypatch.setattr(svc, "_build_ws_client", lambda: None)
    out = asyncio.run(svc.run_once())
    assert out["ok"] is False
    assert out["reason"] == "ws_client_unavailable"


@pytest.mark.slow
def test_user_stream_run_forever_stops_and_closes_client(monkeypatch, tmp_path):
    cfg = usws.UserStreamWSConfig(exchange_id="coinbase", exec_db=str(tmp_path / "exec.sqlite"), retry_sleep_sec=0.01)
    svc = usws.UserStreamFillService(cfg)
    fake = _FakeWSClient()
    monkeypatch.setattr(svc, "_build_ws_client", lambda: fake)
    monkeypatch.setattr(usws, "route_ccxt_trade", lambda *args, **kwargs: {"ok": True})

    async def _run():
        task = asyncio.create_task(svc.run_forever())
        await asyncio.sleep(0.02)
        svc.stop()
        return await task

    out = asyncio.run(_run())
    assert out["ok"] is True
    assert fake.closed is True
    assert out["loops"] >= 1
