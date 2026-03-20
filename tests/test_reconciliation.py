from __future__ import annotations

from services.execution import reconciliation


class _FakeExchange:
    def __init__(self, balance: dict):
        self.balance = dict(balance)
        self.closed = False

    def fetch_balance(self):
        return dict(self.balance)

    def close(self):
        self.closed = True


class _FakePositionStateSQLite:
    def __init__(self):
        self.rows: list[dict] = []

    def upsert(self, **kwargs):
        self.rows.append(dict(kwargs))


def test_reconcile_spot_position_returns_missing_credentials_without_building_exchange(monkeypatch):
    seen: dict = {"called": False}

    monkeypatch.setattr(
        reconciliation,
        "load_exchange_credentials",
        lambda venue: {
            "source": "env",
            "api_env": "COINBASE_API_KEY",
            "secret_env": "COINBASE_API_SECRET",
            "apiKey": "",
            "secret": "",
        },
    )

    def _unexpected_make_exchange(*args, **kwargs):
        seen["called"] = True
        raise AssertionError("make_exchange should not be called without credentials")

    monkeypatch.setattr(reconciliation, "make_exchange", _unexpected_make_exchange)

    out = reconciliation.reconcile_spot_position(venue="coinbase", symbol="BTC/USD")

    assert out["ok"] is False
    assert out["error"] == "missing_credentials"
    assert out["source"] == "env"
    assert seen["called"] is False


def test_reconcile_spot_position_uses_loaded_credentials(monkeypatch):
    fake_exchange = _FakeExchange(
        {
            "total": {"BTC": 1.25},
            "free": {"BTC": 1.0},
            "used": {"BTC": 0.25},
        }
    )
    fake_store = _FakePositionStateSQLite()
    seen: dict = {}

    monkeypatch.setattr(
        reconciliation,
        "load_exchange_credentials",
        lambda venue: {
            "source": "keyring",
            "apiKey": "k",
            "secret": "s",
            "password": "p",
        },
    )

    def _fake_make_exchange(venue, creds, enable_rate_limit=True):
        seen["venue"] = venue
        seen["creds"] = dict(creds)
        seen["enable_rate_limit"] = enable_rate_limit
        return fake_exchange

    monkeypatch.setattr(reconciliation, "make_exchange", _fake_make_exchange)
    monkeypatch.setattr(reconciliation, "PositionStateSQLite", lambda: fake_store)

    out = reconciliation.reconcile_spot_position(venue="coinbase", symbol="BTC/USD")

    assert out["ok"] is True
    assert out["qty"] == 1.25
    assert out["status"] == "open"
    assert seen["venue"] == "coinbase"
    assert seen["creds"] == {"apiKey": "k", "secret": "s", "password": "p"}
    assert seen["enable_rate_limit"] is True
    assert fake_store.rows[0]["note"] == "reconciled_from_balance"
    assert fake_exchange.closed is True
