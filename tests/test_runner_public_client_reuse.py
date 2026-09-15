from services.execution import strategy_runner as runner


def test_reuse_recovery_and_cleanup(monkeypatch):
    made = []

    class Client:
        calls = 0
        closed = 0

        def fetch_ohlcv(self, *args, **kwargs):
            self.calls += 1
            if self.calls == 1:
                raise ConnectionError("temporary")
            return [[1789400000000, 1, 1, 1, 1, 1]]

        def close(self):
            self.closed += 1

    def factory(venue, creds, **kwargs):
        assert creds == {"apiKey": None, "secret": None}
        assert kwargs == {"enable_rate_limit": True}
        client = Client()
        made.append(client)
        return client

    monkeypatch.setattr(runner, "make_exchange", factory)
    monkeypatch.setattr(runner, "_sample_ohlcv_env_enabled", lambda: False)
    monkeypatch.setattr(runner, "_persist_public_ohlcv_snapshot", lambda *a, **k: None)
    cfg = dict(venue="gateio", symbol="BTC/USDT", signal_source="public_ohlcv_5m", min_bars=1, max_bars=5)
    pool = runner._PublicOHLCVClients()
    assert runner._fetch_public_ohlcv(cfg, clients=pool)[0] == []
    rows, source = runner._fetch_public_ohlcv(cfg, clients=pool)
    assert rows and source["source"] == "public_ohlcv"
    assert len(made) == 1 and made[0].closed == 0
    assert pool.get("binance") is not pool.get("gateio")
    pool.close()
    pool.close()
    assert [c.closed for c in made] == [1, 1]


def test_cleanup_continues_after_close_error(monkeypatch):
    closed = []

    class Client:
        def close(self):
            closed.append(True)
            raise RuntimeError("close failed")

    monkeypatch.setattr(runner, "make_exchange", lambda *a, **k: Client())
    pool = runner._PublicOHLCVClients()
    pool.get("gateio")
    pool.get("binance")
    pool.close()
    assert len(closed) == 2
