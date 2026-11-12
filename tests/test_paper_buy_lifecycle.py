"""Real SQLite paper queue/engine tests; no provider or process is contacted."""
import importlib
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest


@pytest.fixture
def rig(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as paths
    import storage.intent_queue_sqlite as queue
    import storage.paper_trading_sqlite as ledger
    import storage.trade_journal_sqlite as journal
    import services.execution.paper_engine as engine
    import services.execution.paper_runner as runner
    import services.execution.intent_reconciler as reconciler
    for module in (paths, queue, ledger, journal, engine, runner, reconciler):
        importlib.reload(module)
    now = [datetime.now(timezone.utc)]
    clock = lambda: now[0].isoformat()
    monkeypatch.setattr(runner, "_now", clock)
    monkeypatch.setattr(reconciler, "_now", clock)
    monkeypatch.setattr(engine, "load_user_yaml", lambda: {"paper_trading": {
        "starting_cash_quote": 1000, "fee_bps": 50, "slippage_bps": 0, "use_ccxt_fallback": False}})
    monkeypatch.setattr(engine.PaperEngine, "_pre_submit_gate", lambda *a, **kw: (True, None))
    monkeypatch.setattr(engine.PaperEngine, "_price", lambda *a: {"bid": 100, "ask": 100, "last": 100})
    async def allowed(*args, **kwargs):
        return SimpleNamespace(allowed=True)
    monkeypatch.setattr(runner, "decide_order", allowed)
    import services.alerts.alert_dispatcher as alerts
    import services.admin.config_editor as config
    monkeypatch.setattr(config, "load_user_yaml", lambda **kw: {})
    dispatches = []
    monkeypatch.setattr(alerts, "send_alert", lambda **kw: dispatches.append(kw) or {"ok": True, "skipped": True})
    qdb, eng, jdb = queue.IntentQueueSQLite(), engine.PaperEngine(clock=clock), journal.TradeJournalSQLite()
    return SimpleNamespace(q=qdb, eng=eng, j=jdb, runner=runner, rec=reconciler, now=now,
                           clock=clock, alerts=dispatches)


def seed(rig, iid="buy", *, age=0, side="buy", status="queued"):
    created = (rig.now[0] - timedelta(seconds=age)).isoformat()
    rig.q.upsert_intent({"intent_id": iid, "created_ts": created, "ts": created,
        "source": "strategy", "strategy_id": "test", "venue": "coinbase", "symbol": "ADA/USD",
        "side": side, "order_type": "market", "qty": 1, "status": status})
    return rig.q.get_intent(iid)


@pytest.mark.parametrize("status", ["queued", "submitting", "held"])
def test_restart_expires_unwritten_old_buy_with_receipt_and_alert(rig, status):
    seed(rig, age=180, status=status)
    rig.runner._consume_queued_intents_once(qdb=rig.q, eng=rig.eng)
    row = rig.q.get_intent("buy")
    assert row["status"] == "expired"
    assert "expired" in row["last_error"]
    assert rig.eng.db.list_orders() == []
    assert rig.eng.db.list_fills() == []
    assert rig.eng.cash_quote() == 1000
    assert len(rig.alerts) == 1
    events = rig.q.list_paper_buy_events("buy")
    assert any(e["status"] == "expired" and e["event"] == "transition" for e in events)
    assert events[-1]["reason"] == "not_delivered"


def test_route_delay_cannot_refresh_original_creation_time(rig, monkeypatch):
    seed(rig)
    async def delayed(*a, **kw):
        rig.now[0] += timedelta(seconds=121)
        return SimpleNamespace(allowed=True)
    monkeypatch.setattr(rig.runner, "decide_order", delayed)
    rig.runner._consume_queued_intents_once(qdb=rig.q, eng=rig.eng)
    assert rig.q.get_intent("buy")["status"] == "expired"
    assert rig.eng.db.list_orders() == []


def test_limit_expires_without_quote_or_cross_and_cannot_later_fill(rig, monkeypatch):
    seed(rig)
    rig.runner._consume_queued_intents_once(qdb=rig.q, eng=rig.eng)
    order = rig.eng.db.get_order_by_client_id("paper_intent_buy")
    monkeypatch.setattr(rig.eng, "_price", lambda *a: None)
    rig.now[0] += timedelta(seconds=120)
    rig.eng.evaluate_open_orders()
    assert rig.eng.db.get_order_by_client_id("paper_intent_buy")["status"] == "expired"
    result = rig.eng._apply_fill(order, 100, 1)
    assert not result["ok"]
    assert rig.eng.db.list_fills() == []
    assert rig.eng.cash_quote() == 1000


@pytest.mark.parametrize("stage", ["new", "filled"])
def test_crash_after_ledger_write_recovers_without_second_order_or_fill(rig, stage):
    row = seed(rig)
    rig.q.claim_next_queued()
    response = rig.eng.submit_order(client_order_id="paper_intent_buy", venue="coinbase", symbol="ADA/USD",
        side="buy", order_type="market", qty=1, intent_created_ts=row["created_ts"])
    assert response["ok"]
    if stage == "filled":
        assert rig.eng.evaluate_open_orders()["filled"] == 1
    out = rig.rec.reconcile_once(qdb=rig.q, pdb=rig.eng.db, jdb=rig.j)
    assert out["buy_recovery_faults"] == []
    assert rig.q.get_intent("buy")["status"] == ("filled" if stage == "filled" else "submitted")
    if stage == "new":
        assert rig.eng.evaluate_open_orders()["filled"] == 1
        rig.rec.reconcile_once(qdb=rig.q, pdb=rig.eng.db, jdb=rig.j)
    rig.runner._consume_queued_intents_once(qdb=rig.q, eng=rig.eng)
    rig.rec.reconcile_once(qdb=rig.q, pdb=rig.eng.db, jdb=rig.j)
    assert len(rig.eng.db.list_orders()) == len(rig.eng.db.list_fills()) == rig.j.count() == 1
    assert rig.eng.cash_quote() == 899.5
    assert rig.eng.db.get_position("ADA/USD")["qty"] == 1
    events = rig.q.list_paper_buy_events("buy")
    assert sum(e["event"] == "picked_up" for e in events) == 1
    assert sum(e["status"] == "filled" for e in events) == 1


def test_old_sell_is_not_expired(rig):
    rig.eng.db.upsert_position("ADA/USD", 1, 100, 0)
    seed(rig, "sell", age=86400, side="sell")
    rig.runner._consume_queued_intents_once(qdb=rig.q, eng=rig.eng)
    assert rig.eng.evaluate_open_orders()["filled"] == 1
    rig.rec.reconcile_once(qdb=rig.q, pdb=rig.eng.db, jdb=rig.j)
    assert rig.q.get_intent("sell")["status"] == "filled"


def test_expired_queue_cannot_be_resurrected(rig):
    original = seed(rig, age=180)
    rig.runner._consume_queued_intents_once(qdb=rig.q, eng=rig.eng)
    assert not rig.q.update_status("buy", "submitted")
    rig.q.upsert_intent({**original, "created_ts": rig.clock(), "status": "queued"})
    assert rig.q.get_intent("buy")["status"] == "expired"


def test_missing_linked_order_is_reported_not_assumed_unwritten(rig):
    row = seed(rig, status="submitted", age=180)
    rig.q.update_status(row["intent_id"], "submitted", linked_order_id="missing")
    result = rig.rec.reconcile_once(qdb=rig.q, pdb=rig.eng.db, jdb=rig.j)
    assert result["buy_recovery_faults"] == [{"intent_id": "buy", "reason": "paper_buy_linked_order_missing"}]
    assert rig.q.get_intent("buy")["status"] == "submitted"
    assert rig.alerts


@pytest.mark.parametrize("filled", [False, True])
def test_submit_exception_after_commit_recovers_before_disposal(rig, monkeypatch, filled):
    seed(rig)
    submit = rig.eng.submit_order
    def uncertain(**kwargs):
        result = submit(**kwargs)
        assert result["ok"]
        if filled:
            assert rig.eng.evaluate_open_orders()["filled"] == 1
        raise RuntimeError("lost_response_after_commit")
    monkeypatch.setattr(rig.eng, "submit_order", uncertain)
    rig.runner._consume_queued_intents_once(qdb=rig.q, eng=rig.eng)
    assert rig.q.get_intent("buy")["status"] == "submitted"
    assert any(e["event"] == "submit_uncertain" for e in rig.q.list_paper_buy_events("buy"))
    rig.rec.reconcile_once(qdb=rig.q, pdb=rig.eng.db, jdb=rig.j)
    if not filled:
        assert rig.eng.evaluate_open_orders()["filled"] == 1
        rig.rec.reconcile_once(qdb=rig.q, pdb=rig.eng.db, jdb=rig.j)
    rig.runner._consume_queued_intents_once(qdb=rig.q, eng=rig.eng)
    assert rig.q.get_intent("buy")["status"] == "filled"
    assert len(rig.eng.db.list_fills()) == len(rig.eng.db.list_orders()) == rig.j.count() == 1
    assert rig.eng.cash_quote() == 899.5


def test_resting_limit_original_queue_age_survives_recovery_restart(rig):
    from services.execution.paper_buy_lifecycle import recover_paper_buys
    row = seed(rig, age=90)
    rig.q.upsert_intent({**row, "order_type": "limit", "limit_price": 50})
    rig.q.claim_next_queued()
    result = rig.eng.submit_order(client_order_id="paper_intent_buy", venue="coinbase", symbol="ADA/USD",
                                  side="buy", order_type="limit", qty=1, limit_price=50)
    assert result["ok"]
    # Legacy order knew only its own later creation. Recovery must bind the older intent.
    recover_paper_buys(rig.q, rig.eng.db, clock=rig.clock)
    rig.now[0] += timedelta(seconds=31)
    rig.eng.evaluate_open_orders()
    assert rig.eng.db.get_order_by_client_id("paper_intent_buy")["status"] == "expired"
    assert rig.eng.db.list_fills() == []


def test_terminal_alert_dispatch_failure_is_retained_and_retried(rig, monkeypatch):
    from services.execution.paper_buy_lifecycle import recover_paper_buys
    import services.alerts.alert_dispatcher as alerts
    seed(rig, age=180)
    def failed(**kwargs):
        raise ConnectionError("synthetic")
    monkeypatch.setattr(alerts, "send_alert", failed)
    recover_paper_buys(rig.q, rig.eng.db, clock=rig.clock)
    assert rig.q.get_intent("buy")["status"] == "expired"
    assert rig.q.list_paper_buy_events("buy")[-1]["event"] == "alert_error"
    delivered = []
    monkeypatch.setattr(alerts, "send_alert", lambda **kw: delivered.append(kw) or {"ok": True})
    rig.now[0] += timedelta(seconds=121)
    recover_paper_buys(rig.q, rig.eng.db, clock=rig.clock)
    recover_paper_buys(rig.q, rig.eng.db, clock=rig.clock)
    assert len(delivered) == 1
    assert rig.q.list_paper_buy_events("buy")[-1]["reason"] == "external_channel_accepted"
    assert rig.eng.db.list_fills() == []


def test_router_refusal_has_durable_reason_and_dispatch_receipt(rig, monkeypatch):
    seed(rig)
    async def refused(*a, **kw):
        return SimpleNamespace(allowed=False, reason="synthetic_block")
    monkeypatch.setattr(rig.runner, "decide_order", refused)
    rig.runner._consume_queued_intents_once(qdb=rig.q, eng=rig.eng)
    assert rig.q.get_intent("buy")["status"] == "rejected"
    assert rig.q.get_intent("buy")["last_error"] == "decide_order:synthetic_block"
    assert len(rig.alerts) == 1
    assert rig.q.list_paper_buy_events("buy")[-1]["reason"] == "not_delivered"


def test_recently_picked_up_old_buy_is_not_a_minute_stranded(rig):
    from services.execution.paper_buy_lifecycle import recover_paper_buys
    seed(rig, age=90)
    rig.q.claim_next_queued()
    recover_paper_buys(rig.q, rig.eng.db, clock=rig.clock)
    assert rig.q.get_intent("buy")["status"] == "submitting"
    assert not rig.alerts


def test_newly_submitted_buy_after_inventory_is_still_identity_checked(rig, monkeypatch):
    seed(rig)
    rig.q.claim_next_queued()
    order = rig.eng.submit_order(client_order_id="paper_intent_buy", venue="coinbase", symbol="BTC/USD",
                                  side="buy", order_type="market", qty=1)["order"]
    rig.eng.evaluate_open_orders()
    rig.q.update_status("buy", "submitted", linked_order_id=order["order_id"])
    monkeypatch.setattr(rig.q, "list_pending_paper_buys", lambda: [])
    result = rig.rec.reconcile_once(qdb=rig.q, pdb=rig.eng.db, jdb=rig.j)
    assert result["buy_recovery_faults"] == [{"intent_id": "buy", "reason": "paper_buy_order_identity_mismatch"}]
    assert rig.q.get_intent("buy")["status"] == "submitted"
    assert rig.j.count() == 0


def test_filled_flag_without_a_fill_receipt_cannot_complete_buy(rig):
    row = seed(rig)
    rig.q.claim_next_queued()
    order = rig.eng.submit_order(client_order_id="paper_intent_buy", venue="coinbase", symbol="ADA/USD",
                                  side="buy", order_type="market", qty=1,
                                  intent_created_ts=row["created_ts"])["order"]
    rig.eng.db.update_order_status(order["order_id"], "filled")
    rig.q.update_status("buy", "submitted", linked_order_id=order["order_id"])
    result = rig.rec.reconcile_once(qdb=rig.q, pdb=rig.eng.db, jdb=rig.j)
    assert result["buy_recovery_faults"] == [{"intent_id": "buy", "reason": "paper_buy_fill_receipt_mismatch"}]
    assert rig.q.get_intent("buy")["status"] == "submitted"
    assert rig.j.count() == 0
