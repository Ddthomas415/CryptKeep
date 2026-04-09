from __future__ import annotations

import builtins

from scripts import cancel_intent, reconcile_order_dedupe
from services.execution import live_executor as le


def test_cancel_intent_main_passes_sandbox_to_exchange_client(monkeypatch):
    captured: dict[str, object] = {}

    class _FakeOpen:
        def read(self) -> str:
            return "execution:\n  db_path: /tmp/execution.sqlite\n"

    class _FakeClient:
        def __init__(self, exchange_id: str, sandbox: bool = False):
            captured["exchange_id"] = exchange_id
            captured["sandbox"] = sandbox

        def cancel_intent(self, *, exec_db: str, intent_id: str, symbol: str):
            captured["exec_db"] = exec_db
            captured["intent_id"] = intent_id
            captured["symbol"] = symbol
            return {"ok": True}

    monkeypatch.setattr(builtins, "open", lambda *args, **kwargs: _FakeOpen())
    monkeypatch.setattr(cancel_intent, "ExchangeClient", _FakeClient)

    out = cancel_intent.main(["--exchange", "binance", "--symbol", "BTC/USDT", "--intent-id", "intent-1", "--sandbox"])

    assert out == 0
    assert captured == {
        "exchange_id": "binance",
        "sandbox": True,
        "exec_db": "/tmp/execution.sqlite",
        "intent_id": "intent-1",
        "symbol": "BTC/USDT",
    }


def test_reconcile_order_dedupe_main_passes_sandbox_to_exchange_client(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    class _FakeStore:
        def __init__(self, exec_db: str):
            captured["exec_db"] = exec_db

        def list_needs_reconcile(self, *, exchange_id: str, limit: int = 100):
            captured["exchange_id"] = exchange_id
            captured["limit"] = limit
            return []

    class _FakeClient:
        def __init__(self, exchange_id: str, sandbox: bool = False):
            captured["client_exchange_id"] = exchange_id
            captured["sandbox"] = sandbox

        def fetch_open_orders(self, *, symbol: str, since=None, limit=None):
            captured["symbol"] = symbol
            return []

    monkeypatch.setattr(reconcile_order_dedupe, "OrderDedupeStore", _FakeStore)
    monkeypatch.setattr(reconcile_order_dedupe, "ExchangeClient", _FakeClient)

    out = reconcile_order_dedupe.main(
        [
            "--exchange",
            "binance",
            "--symbol",
            "BTC/USDT",
            "--exec-db",
            str(tmp_path / "execution.sqlite"),
            "--limit",
            "5",
            "--sandbox",
        ]
    )

    assert out == 0
    assert captured["client_exchange_id"] == "binance"
    assert captured["sandbox"] is True
    assert captured["exchange_id"] == "binance"
    assert captured["limit"] == 5
    assert captured["symbol"] == "BTC/USDT"


def test_reconcile_open_orders_passes_sandbox_to_exchange_client(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    class _FakeStore:
        def list_needs_reconcile(self, *, exchange_id: str, limit: int = 200):
            return []

    class _FakeClient:
        def __init__(self, exchange_id: str, sandbox: bool = False):
            captured["exchange_id"] = exchange_id
            captured["sandbox"] = sandbox

    monkeypatch.setattr(le, "OrderDedupeStore", lambda exec_db: _FakeStore())
    monkeypatch.setattr(le, "ExchangeClient", _FakeClient)

    out = le.reconcile_open_orders(str(tmp_path / "execution.sqlite"), "binance", limit=10, sandbox=True)

    assert out["ok"] is True
    assert captured == {"exchange_id": "binance", "sandbox": True}
