from storage.order_dedupe_store_sqlite import OrderDedupeStore

def test_claim_is_stable(tmp_path):
    db = str(tmp_path / "x.sqlite")
    s = OrderDedupeStore(exec_db=db)
    r1 = s.claim(exchange_id="binance", intent_id="i1", symbol="BTC/USDT", client_order_id="c1")
    r2 = s.claim(exchange_id="binance", intent_id="i1", symbol="BTC/USDT", client_order_id="c1")
    assert r1["intent_id"] == r2["intent_id"]
    assert r2["client_order_id"] == "c1"

def test_mark_submitted(tmp_path):
    db = str(tmp_path / "x.sqlite")
    s = OrderDedupeStore(exec_db=db)
    s.claim(exchange_id="binance", intent_id="i1", symbol="BTC/USDT", client_order_id="c1")
    s.mark_submitted(exchange_id="binance", intent_id="i1", remote_order_id="r1")
    r = s.get_by_intent("binance", "i1")
    assert r["remote_order_id"] == "r1"
    assert r["status"] in ("submitted", "acked", "terminal")
