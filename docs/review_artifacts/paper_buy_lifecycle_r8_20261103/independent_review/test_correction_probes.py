"""Bounded independent correction checks; real isolated stores, no providers."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import sqlite3
import threading

import pytest

from tests.test_paper_buy_lifecycle import rig, seed


def order_for(rig, client="paper_intent_buy", side="buy"):
    result = rig.eng.submit_order(client_order_id=client, venue="coinbase", symbol="ADA/USD",
                                  side=side, order_type="market", qty=1)
    assert result["ok"]
    return result["order"]


@pytest.mark.parametrize("client", ["paper_intent_buy", "custom-client"])
@pytest.mark.parametrize("operation", ["fill", "expire"])
@pytest.mark.parametrize("origin,reason", [("old", "expired"), ("future", "future_created_ts"),
                                           ("invalid", "invalid_created_ts")])
def test_gate_queue_origin_read_after_waiting_for_ledger_lock(rig, monkeypatch, client, operation, origin, reason):
    import storage.paper_trading_sqlite as ledger
    import storage.intent_queue_sqlite as queue
    seed(rig)
    rig.q.claim_next_queued()
    with sqlite3.connect(queue.DB_PATH) as con:
        con.execute("UPDATE trade_intents SET client_order_id=? WHERE intent_id='buy'", (client,))
    order = order_for(rig, client)
    writer = ledger._connect()
    writer.execute("BEGIN IMMEDIATE")
    started = threading.Event()
    original = ledger._connect

    def connect():
        started.set()
        return original()

    monkeypatch.setattr(ledger, "_connect", connect)
    value = ((rig.now[0] - timedelta(seconds=121)).isoformat() if origin == "old" else
             (rig.now[0] + timedelta(seconds=1)).isoformat() if origin == "future" else "broken")
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            work = (pool.submit(rig.eng._apply_fill, order, 100, 1) if operation == "fill" else
                    pool.submit(rig.eng.db.expire_buy_order, client, clock=rig.clock))
            assert started.wait(3)
            with sqlite3.connect(queue.DB_PATH) as con:
                con.execute("UPDATE trade_intents SET created_ts=? WHERE intent_id='buy'", (value,))
            writer.execute("COMMIT")
            result = work.result(timeout=5)
    finally:
        writer.close()
    assert result["reason"] == "paper_buy_ttl:" + reason
    assert rig.eng.db.list_fills() == []
    assert rig.eng.cash_quote() == 1000


@pytest.mark.parametrize("damage", ["missing", "unreadable"])
def test_gate_canonical_missing_or_unreadable_queue_is_read_only_unresolved(rig, damage):
    import storage.intent_queue_sqlite as queue
    seed(rig)
    order = order_for(rig)
    with sqlite3.connect(queue.DB_PATH) as con:
        con.execute("DELETE FROM trade_intents" if damage == "missing" else
                    "ALTER TABLE trade_intents RENAME TO unavailable")
    result = rig.eng._apply_fill(order, 100, 1)
    assert result == {"ok": False, "reason": "paper_buy_queue_origin_" + damage}
    assert rig.eng.db.get_order_by_order_id(order["order_id"])["status"] == "new"
    assert rig.eng.db.list_fills() == []
    with sqlite3.connect(queue.DB_PATH) as con:
        if damage == "missing":
            assert con.execute("SELECT COUNT(*) FROM trade_intents").fetchone()[0] == 0
        else:
            assert con.execute("SELECT COUNT(*) FROM unavailable").fetchone()[0] == 1


def test_gate_no_canonical_receipt_after_inventory_blocks_attribution(rig, monkeypatch):
    import storage.paper_trading_sqlite as ledger
    seed(rig)
    rig.q.claim_next_queued()
    order = order_for(rig)
    assert rig.eng.evaluate_open_orders()["filled"] == 1
    rig.q.update_status("buy", "submitted", linked_order_id=order["order_id"])
    # Simulate a row arriving after the recovery inventory, with no matching client receipt.
    monkeypatch.setattr(rig.q, "list_pending_paper_buys", lambda: [])
    with sqlite3.connect(ledger.DB_PATH) as con:
        con.execute("UPDATE paper_orders SET client_order_id='unrelated' WHERE order_id=?", (order["order_id"],))
    result = rig.rec.reconcile_once(qdb=rig.q, pdb=rig.eng.db, jdb=rig.j)
    assert result["buy_recovery_faults"] == [{"intent_id": "buy", "reason": "paper_buy_order_identity_mismatch"}]
    assert rig.q.get_intent("buy")["status"] == "submitted"
    assert rig.j.count() == 0


@pytest.mark.parametrize("field,value", [("qty", 0.5), ("price", 0), ("fee", float("inf"))])
def test_gate_actual_malformed_full_fill_receipt_stays_unresolved(rig, monkeypatch, field, value):
    import storage.paper_trading_sqlite as ledger
    seed(rig)
    rig.q.claim_next_queued()
    order = order_for(rig)
    assert rig.eng.evaluate_open_orders()["filled"] == 1
    rig.q.update_status("buy", "submitted", linked_order_id=order["order_id"])
    monkeypatch.setattr(rig.q, "list_pending_paper_buys", lambda: [])
    assert field in {"qty", "price", "fee"}
    with sqlite3.connect(ledger.DB_PATH) as con:
        con.execute("UPDATE paper_fills SET " + field + "=? WHERE order_id=?", (value, order["order_id"]))
    result = rig.rec.reconcile_once(qdb=rig.q, pdb=rig.eng.db, jdb=rig.j)
    assert result["buy_recovery_faults"] == [{"intent_id": "buy", "reason": "paper_buy_fill_receipt_mismatch"}]
    assert rig.q.get_intent("buy")["status"] == "submitted"
    assert rig.j.count() == 0


def test_gate_custom_client_valid_receipt_reconciles_normally(rig):
    import storage.intent_queue_sqlite as queue
    seed(rig)
    rig.q.claim_next_queued()
    with sqlite3.connect(queue.DB_PATH) as con:
        con.execute("UPDATE trade_intents SET client_order_id='custom-client' WHERE intent_id='buy'")
    order = order_for(rig, "custom-client")
    assert rig.eng.evaluate_open_orders()["filled"] == 1
    rig.q.update_status("buy", "submitted", linked_order_id=order["order_id"])
    result = rig.rec.reconcile_once(qdb=rig.q, pdb=rig.eng.db, jdb=rig.j)
    assert not result["buy_recovery_faults"]
    assert rig.q.get_intent("buy")["status"] == "filled"
    assert rig.j.count() == 1


@pytest.mark.parametrize("side", ["buy", "sell"])
def test_gate_direct_noncanonical_fallback_and_sell_queue_independence(rig, side):
    import storage.intent_queue_sqlite as queue
    if side == "sell":
        rig.eng.db.upsert_position("ADA/USD", 1, 100, 0)
    order = order_for(rig, "direct-order", side=side)
    if side == "sell":
        with sqlite3.connect(queue.DB_PATH) as con:
            con.execute("ALTER TABLE trade_intents RENAME TO unavailable")
    assert rig.eng._apply_fill(order, 100, 1)["ok"]
    assert len(rig.eng.db.list_fills()) == 1
