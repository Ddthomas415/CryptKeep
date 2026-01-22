from storage.order_dedupe_store_sqlite import OrderDedupeStore

def test_mark_unknown(tmp_path):
    db = str(tmp_path / "x.sqlite")
    s = OrderDedupeStore(exec_db=db)
    s.claim(exchange_id="binance", intent_id="i1", symbol="BTC/USDT", client_order_id="c1")
    s.mark_unknown(exchange_id="binance", intent_id="i1", error="timeout")
    r = s.get_by_intent("binance", "i1")
    assert r["status"] == "unknown"
    assert "timeout" in (r.get("last_error") or "")
