from __future__ import annotations

import pytest

from services.execution.order_params import OrderParamError, prepare_ccxt_params


def test_prepare_ccxt_params_coinbase_default_key_and_filtering():
    out = prepare_ccxt_params(
        exchange_id="coinbase",
        client_order_id="cid-1",
        order_type="limit",
        price=100.0,
        params={"timeInForce": "gtc", "foo": 1},
    )
    assert out["clientOrderId"] == "cid-1"
    assert out["timeInForce"] == "GTC"
    assert "foo" not in out


def test_prepare_ccxt_params_binance_uses_new_client_order_id():
    out = prepare_ccxt_params(
        exchange_id="binanceus",
        client_order_id="cid-2",
        order_type="limit",
        price=10.0,
        params={"postOnly": True},
    )
    assert out["newClientOrderId"] == "cid-2"
    assert out["postOnly"] is True
    assert "clientOrderId" not in out


def test_prepare_ccxt_params_gate_uses_text():
    out = prepare_ccxt_params(
        exchange_id="gateio",
        client_order_id="cid-3",
        order_type="limit",
        price=10.0,
        params={},
    )
    assert out["text"] == "cid-3"


def test_prepare_ccxt_params_post_only_requires_limit_and_price():
    with pytest.raises(OrderParamError, match="postOnly requires a LIMIT order"):
        prepare_ccxt_params(
            exchange_id="coinbase",
            client_order_id="cid-4",
            order_type="market",
            price=None,
            params={"postOnly": True},
        )

    with pytest.raises(OrderParamError, match="postOnly requires price"):
        prepare_ccxt_params(
            exchange_id="coinbase",
            client_order_id="cid-5",
            order_type="limit",
            price=None,
            params={"postOnly": True},
        )


def test_prepare_ccxt_params_rejects_unsupported_tif():
    with pytest.raises(OrderParamError, match="unsupported timeInForce"):
        prepare_ccxt_params(
            exchange_id="coinbase",
            client_order_id="cid-6",
            order_type="limit",
            price=1.0,
            params={"timeInForce": "DAY"},
        )
