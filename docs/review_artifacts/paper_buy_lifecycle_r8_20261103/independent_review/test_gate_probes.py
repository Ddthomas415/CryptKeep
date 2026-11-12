"""Independent R8 boundary probes; synthetic inputs and temporary real SQLite."""
from datetime import timedelta
import sqlite3

import pytest

from tests.test_paper_buy_lifecycle import rig, seed
from services.execution.paper_buy_lifecycle import recover_paper_buys


def submit(rig, client, **changes):
    args = dict(client_order_id=client, venue="coinbase", symbol="ADA/USD",
                side="buy", order_type="market", qty=1)
    args.update(changes)
    result = rig.eng.submit_order(**args)
    assert result["ok"]
    return result["order"]


@pytest.mark.parametrize("mismatch", ["wrong_link", "wrong_qty"])
def test_gate_identity_fault_must_block_reconciliation(rig, mismatch):
    seed(rig)
    rig.q.claim_next_queued()
    canonical = submit(rig, "paper_intent_buy", qty=2 if mismatch == "wrong_qty" else 1)
    linked = (submit(rig, "unrelated", symbol="BTC/USD")
              if mismatch == "wrong_link" else canonical)
    assert rig.eng.evaluate_open_orders()["filled"] >= 1
    assert rig.q.update_status("buy", "submitted", linked_order_id=linked["order_id"])
    result = rig.rec.reconcile_once(qdb=rig.q, pdb=rig.eng.db, jdb=rig.j)
    assert result["buy_recovery_faults"] == [
        {"intent_id": "buy", "reason": "paper_buy_order_identity_mismatch"}]
    assert (rig.q.get_intent("buy")["status"], rig.j.count()) == ("submitted", 0), result


def test_gate_pickup_over_60_alerts_without_disposal(rig):
    import storage.intent_queue_sqlite as queue
    seed(rig, age=110)
    rig.q.claim_next_queued()
    with sqlite3.connect(queue.DB_PATH) as con:
        con.execute("UPDATE trade_intents SET updated_ts=? WHERE intent_id='buy'",
                    ((rig.now[0] - timedelta(seconds=61)).isoformat(),))
    result = recover_paper_buys(rig.q, rig.eng.db, clock=rig.clock)
    assert not result["faults"]
    assert rig.q.get_intent("buy")["status"] == "submitting"
    assert rig.alerts[-1]["payload"]["reason"] == "paper_buy_submitting_over_60s"
    assert rig.eng.db.list_fills() == []


def test_gate_unreadable_queue_never_touches_ledger(rig, monkeypatch):
    seed(rig)
    def unreadable():
        raise sqlite3.DatabaseError("synthetic")
    monkeypatch.setattr(rig.q, "list_pending_paper_buys", unreadable)
    result = recover_paper_buys(rig.q, rig.eng.db, clock=rig.clock)
    assert result["faults"] == [{"reason": "buy_inventory_unreadable:DatabaseError"}]
    assert rig.eng.db.list_orders() == []
    assert rig.q.get_intent("buy")["status"] == "queued"


def test_gate_malformed_origin_fenced_without_fill(rig):
    import storage.intent_queue_sqlite as queue
    seed(rig)
    with sqlite3.connect(queue.DB_PATH) as con:
        con.execute("UPDATE trade_intents SET created_ts='broken' WHERE intent_id='buy'")
    recover_paper_buys(rig.q, rig.eng.db, clock=rig.clock)
    assert rig.q.get_intent("buy")["status"] == "rejected"
    order = submit(rig, "paper_intent_buy")
    assert not rig.eng._apply_fill(order, 100, 1)["ok"]
    assert rig.eng.db.list_fills() == []


def test_gate_terminal_write_refusal_keeps_durable_ledger_fence(rig, monkeypatch):
    seed(rig, age=180, status="held")
    original = rig.q.update_status
    monkeypatch.setattr(rig.q, "update_status", lambda *a, **kw: False)
    recover_paper_buys(rig.q, rig.eng.db, clock=rig.clock)
    assert rig.q.get_intent("buy")["status"] == "held"
    order = submit(rig, "paper_intent_buy")
    assert not rig.eng._apply_fill(order, 100, 1)["ok"]
    monkeypatch.setattr(rig.q, "update_status", original)
    recover_paper_buys(rig.q, rig.eng.db, clock=rig.clock)
    assert rig.q.get_intent("buy")["status"] == "expired"
    assert not rig.q.update_status("buy", "queued")
    assert rig.eng.db.list_fills() == []


def test_gate_dispatch_response_loss_stays_retryable(rig, monkeypatch):
    import services.alerts.alert_dispatcher as alerts
    attempts = []
    def uncertain(**kw):
        attempts.append(kw)
        raise RuntimeError("response_lost_after_possible_delivery")
    monkeypatch.setattr(alerts, "send_alert", uncertain)
    seed(rig, age=180)
    recover_paper_buys(rig.q, rig.eng.db, clock=rig.clock)
    assert rig.q.list_paper_buys_needing_alert()
    recover_paper_buys(rig.q, rig.eng.db, clock=rig.clock)
    assert len(attempts) == 1
    rig.now[0] += timedelta(seconds=121)
    recover_paper_buys(rig.q, rig.eng.db, clock=rig.clock)
    assert len(attempts) == 2
    assert not any(e["reason"] == "external_channel_accepted"
                   for e in rig.q.list_paper_buy_events("buy"))


def test_gate_legacy_origin_write_failure_must_not_allow_late_fill(rig):
    import storage.paper_trading_sqlite as ledger
    seed(rig, age=110)
    rig.q.claim_next_queued()
    # Legacy order has no reserved origin; its own creation time is recent.
    rig.eng.db.insert_order(dict(order_id="legacy-order", client_order_id="paper_intent_buy",
        ts=rig.clock(), venue="coinbase", symbol="ADA/USD", side="buy",
        order_type="market", qty=1, status="new", meta=None))
    with sqlite3.connect(ledger.DB_PATH) as con:
        con.execute("UPDATE paper_orders SET created_ts=? WHERE order_id='legacy-order'",
                    (rig.clock(),))
        con.execute("CREATE TRIGGER fail_origin BEFORE UPDATE OF meta_json ON paper_orders "
                    "BEGIN SELECT RAISE(ABORT, 'synthetic_transient_write'); END")
    result = recover_paper_buys(rig.q, rig.eng.db, clock=rig.clock)
    assert result["faults"] == [{"intent_id": "buy", "reason": "IntegrityError"}]
    with sqlite3.connect(ledger.DB_PATH) as con:
        con.execute("DROP TRIGGER fail_origin")
    rig.now[0] += timedelta(seconds=11)
    result = rig.eng.evaluate_open_orders()
    assert (result["filled"], len(rig.eng.db.list_fills()), rig.eng.cash_quote()) == (0, 0, 1000), result
