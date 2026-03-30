from unittest.mock import Mock

from services.execution.lifecycle_boundary import fetch_my_trades_via_boundary


def test_fetch_my_trades_via_boundary_calls_exchange_and_returns_rows():
    ex = Mock()
    ex.fetch_my_trades.return_value = [{"id": "t1"}, {"id": "t2"}]

    rows = fetch_my_trades_via_boundary(
        ex,
        venue="coinbase",
        symbol="BTC/USD",
        since_ms=123,
        limit=5,
        source="test",
    )

    ex.fetch_my_trades.assert_called_once_with("BTC/USD", since=123, limit=5)
    assert rows == [{"id": "t1"}, {"id": "t2"}]
