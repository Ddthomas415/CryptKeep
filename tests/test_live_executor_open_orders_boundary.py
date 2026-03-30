from unittest.mock import Mock, patch

from services.execution.lifecycle_boundary import fetch_open_orders_via_boundary


def test_fetch_open_orders_via_boundary_calls_exchange_and_returns_rows():
    ex = Mock()
    ex.fetch_open_orders.return_value = [{"id": "1"}, {"id": "2"}]

    rows = fetch_open_orders_via_boundary(
        ex,
        venue="coinbase",
        symbol="BTC/USD",
        source="test",
    )

    ex.fetch_open_orders.assert_called_once_with("BTC/USD")
    assert rows == [{"id": "1"}, {"id": "2"}]
