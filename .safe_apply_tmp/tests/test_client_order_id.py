from services.execution.client_order_id import make_client_order_id

def test_coinbase_is_uuid():
    cid = make_client_order_id("coinbase", "intent-123")
    assert len(cid) == 36
    assert cid.count("-") == 4

def test_binance_length():
    cid = make_client_order_id("binance", "intent-123")
    assert len(cid) <= 36

def test_gate_length():
    cid = make_client_order_id("gateio", "intent-123")
    assert len(cid) <= 32
