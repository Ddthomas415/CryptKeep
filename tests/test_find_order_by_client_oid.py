from unittest.mock import Mock

from services.execution.exchange_client import ExchangeClient
from services.execution.live_exchange_adapter import LiveExchangeAdapter


def test_exchange_client_find_order_by_client_oid_matches_open_order():
    client = object.__new__(ExchangeClient)
    client.fetch_open_orders = Mock(return_value=[
        {"id": "1", "clientOrderId": "nope"},
        {"id": "2", "info": {"clientOrderId": "cbp-123"}},
    ])

    row = ExchangeClient.find_order_by_client_oid(client, "BTC/USD", "cbp-123")

    client.fetch_open_orders.assert_called_once_with(symbol="BTC/USD")
    assert row == {"id": "2", "info": {"clientOrderId": "cbp-123"}}


def test_live_exchange_adapter_find_order_by_client_oid_matches_open_order():
    adapter = object.__new__(LiveExchangeAdapter)
    adapter.venue = "coinbase"
    adapter.ex = Mock()
    adapter.ex.fetch_open_orders.return_value = [
        {"id": "1", "client_order_id": "cbp-xyz"},
    ]

    row = LiveExchangeAdapter.find_order_by_client_oid(adapter, "BTC/USD", "cbp-xyz")

    adapter.ex.fetch_open_orders.assert_called_once()
    assert row == {"id": "1", "client_order_id": "cbp-xyz"}
