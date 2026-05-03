from __future__ import annotations

from unittest.mock import patch


class _FakeDB:
    def __init__(self):
        self.by_client = {}
        self.by_order = {}
        self.orders = []

    def get_order_by_client_id(self, client_id):
        return self.by_client.get(client_id)

    def get_order_by_order_id(self, order_id):
        return self.by_order.get(order_id)

    def list_orders(self, limit=500, status="new"):
        return [o for o in self.orders if o.get("status") == status][:limit]


class _FakeEngine:
    def __init__(self):
        self.db = _FakeDB()
        self.calls = []

    def submit_order(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "ok": True,
            "order": {
                "order_id": "paper-oid-1",
                "client_order_id": kwargs["client_order_id"],
                "status": "new",
            },
        }


def _adapter():
    from services.execution.adapters.paper import PaperEngineAdapter

    fake = _FakeEngine()
    with patch("services.execution.adapters.paper.PaperEngine", return_value=fake):
        adapter = PaperEngineAdapter(venue="coinbase")
    return adapter, fake


def test_factory_paper_mode_returns_paper_adapter_without_ccxt():
    from services.execution.adapters import factory
    from services.execution.adapters.paper import PaperEngineAdapter

    with patch("services.execution.adapters.paper.PaperEngine", return_value=_FakeEngine()):
        adapter = factory.get_adapter("coinbase", mode="paper")

    assert isinstance(adapter, PaperEngineAdapter)


def test_submit_order_accepts_intent_executor_positional_call():
    adapter, fake = _adapter()

    out = adapter.submit_order("BTC/USD", "buy", 0.001, 60000.0, "limit", "client-123")

    assert out["ok"] is True
    assert out["id"] == "paper-oid-1"
    assert out["clientOrderId"] == "client-123"
    assert fake.calls == [{
        "client_order_id": "client-123",
        "venue": "coinbase",
        "symbol": "BTC/USD",
        "side": "buy",
        "order_type": "limit",
        "qty": 0.001,
        "limit_price": 60000.0,
    }]


def test_find_order_by_client_oid_returns_normalized_order():
    adapter, fake = _adapter()
    fake.db.by_client["coid-1"] = {
        "order_id": "oid-1",
        "client_order_id": "coid-1",
        "status": "new",
        "symbol": "BTC/USD",
        "side": "buy",
        "qty": 0.01,
        "limit_price": None,
        "order_type": "market",
    }

    out = adapter.find_order_by_client_oid("BTC/USD", "coid-1")

    assert out["id"] == "oid-1"
    assert out["clientOrderId"] == "coid-1"
    assert out["_paper"] is True


def test_fetch_open_orders_filters_by_symbol():
    adapter, fake = _adapter()
    fake.db.orders = [
        {"order_id": "o1", "client_order_id": "c1", "status": "new", "symbol": "BTC/USD", "side": "buy", "qty": 1},
        {"order_id": "o2", "client_order_id": "c2", "status": "new", "symbol": "ETH/USD", "side": "buy", "qty": 1},
    ]

    out = adapter.fetch_open_orders("BTC/USD")

    assert len(out) == 1
    assert out[0]["id"] == "o1"


def test_fetch_order_returns_normalized_order():
    adapter, fake = _adapter()
    fake.db.by_order["oid-2"] = {
        "order_id": "oid-2",
        "client_order_id": "coid-2",
        "status": "filled",
        "symbol": "BTC/USD",
        "side": "sell",
        "qty": 0.01,
        "limit_price": None,
        "order_type": "market",
    }

    out = adapter.fetch_order("BTC/USD", "oid-2")

    assert out["id"] == "oid-2"
    assert out["status"] == "filled"


def test_trading_yaml_has_execution_paper_block():
    import yaml
    from pathlib import Path

    cfg = yaml.safe_load(Path("config/trading.yaml").read_text())
    ex = cfg.get("execution")

    assert isinstance(ex, dict)
    assert ex.get("executor_mode") == "paper"
    assert ex.get("venue")
    assert ex.get("symbol")
