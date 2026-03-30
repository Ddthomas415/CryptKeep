from unittest.mock import Mock

from services.execution.lifecycle_boundary import fetch_order_via_boundary


def test_fetch_order_via_boundary_calls_exchange_and_returns_row():
    ex = Mock()
    ex.fetch_order.return_value = {"id": "1", "status": "open"}

    row = fetch_order_via_boundary(
        ex,
        venue="coinbase",
        symbol="BTC/USD",
        order_id="1",
        source="test",
    )

    ex.fetch_order.assert_called_once_with("1", "BTC/USD")
    assert row == {"id": "1", "status": "open"}
