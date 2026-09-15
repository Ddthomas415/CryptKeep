import pytest

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


def test_failed_construction_does_not_poison_pool(monkeypatch):
    attempts = []
    client = object()

    def factory(*args, **kwargs):
        attempts.append(True)
        if len(attempts) == 1:
            raise ConnectionError("construction failed")
        return client

    monkeypatch.setattr(runner, "make_exchange", factory)
    pool = runner._PublicOHLCVClients()
    with pytest.raises(ConnectionError):
        pool.get("gateio")
    assert pool.get("gateio") is client
    assert pool.get("gateio") is client
    assert len(attempts) == 2
    pool.close()


def test_runner_instances_do_not_share_clients(monkeypatch):
    monkeypatch.setattr(runner, "make_exchange", lambda *a, **k: object())
    first = runner._PublicOHLCVClients()
    second = runner._PublicOHLCVClients()
    assert first.get("gateio") is not second.get("gateio")
    first.close()
    second.close()


def test_sample_mode_never_acquires_public_client(monkeypatch):
    def unexpected(*args, **kwargs):
        pytest.fail("sample mode acquired a public client")

    monkeypatch.setattr(runner, "make_exchange", unexpected)
    monkeypatch.setattr(runner, "_sample_ohlcv_env_enabled", lambda: True)
    monkeypatch.setattr(runner, "_persist_public_ohlcv_snapshot", lambda *a, **k: None)
    pool = runner._PublicOHLCVClients()
    _, source = runner._fetch_public_ohlcv(
        dict(venue="gateio", symbol="BTC/USDT", signal_source="public_ohlcv_5m"),
        clients=pool,
    )
    assert source["source"] in ("sample_ohlcv", "none")
    pool.close()
