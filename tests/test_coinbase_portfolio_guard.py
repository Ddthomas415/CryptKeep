from unittest.mock import Mock
import pytest

from services.execution.coinbase_portfolio_guard import (
    enforce_coinbase_quote_account_available,
)


def test_coinbase_blocks_missing_quote_account():
    ex = Mock()
    ex.id = "coinbase"
    ex.v3PrivateGetBrokerageKeyPermissions.return_value = {
        "portfolio_uuid": "p1",
        "can_trade": True,
    }
    ex.fetch_balance.return_value = {
        "info": {
            "data": [
                {"portfolio_id": "p1", "currency": {"code": "ETH"}},
                {"portfolio_id": "p1", "currency": {"code": "SOL"}},
            ]
        }
    }

    with pytest.raises(RuntimeError, match="missing_quote=USD"):
        enforce_coinbase_quote_account_available(ex, "BTC/USD")


def test_coinbase_allows_present_quote_account():
    ex = Mock()
    ex.id = "coinbase"
    ex.v3PrivateGetBrokerageKeyPermissions.return_value = {
        "portfolio_uuid": "p1",
        "can_trade": True,
    }
    ex.fetch_balance.return_value = {
        "info": {
            "data": [
                {"portfolio_id": "p1", "currency": {"code": "BTC"}},
                {"portfolio_id": "p1", "currency": {"code": "USD"}},
            ]
        }
    }

    enforce_coinbase_quote_account_available(ex, "BTC/USD")
