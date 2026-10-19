"""Journal transfer of fill-time cost-policy evidence (CLOUD, 2026-10-09). Isolated temp databases only."""
import copy
import sqlite3

import pytest

from services.execution import intent_reconciler
from storage import intent_queue_sqlite, paper_trading_sqlite, trade_journal_sqlite
from tests.test_journal_execution_identity import identity


@pytest.fixture
def stores(monkeypatch, tmp_path):
    monkeypatch.setattr(intent_queue_sqlite, "DB_PATH", tmp_path / "queue.sqlite")
    monkeypatch.setattr(paper_trading_sqlite, "DB_PATH", tmp_path / "paper.sqlite")
    monkeypatch.setattr(trade_journal_sqlite, "DB_PATH", tmp_path / "journal.sqlite")
    monkeypatch.setattr(intent_reconciler, "log_strategy_outcome", lambda row: None)
    return (intent_queue_sqlite.IntentQueueSQLite(), paper_trading_sqlite.PaperTradingSQLite(),
            trade_journal_sqlite.TradeJournalSQLite())


def run(stores, *, order_meta, fill_evidence, corrupt=False):
    queue, paper, journal = stores
    order = {"order_id": "o1", "client_order_id": "i1", "ts": "2026-10-09T12:00:00Z", "venue": "coinbase",
             "symbol": "BTC/USDT", "side": "buy", "order_type": "market", "qty": 1., "status": "new",
             "meta": order_meta}
    paper.insert_order(order)
    paper.set_state("cash_quote", "1000")
    kwargs = {} if fill_evidence is None else {"execution_identity_evidence": fill_evidence}
    fill = paper.apply_fill(order=order, ts=order["ts"], price=100., qty=1., fee=.075, fee_currency="USDT", **kwargs)
    if corrupt:
        paper.set_state("fill_execution_identity:" + fill["fill_id"], "not json")
    queue.upsert_intent({"intent_id": "i1", "ts": order["ts"], "source": "strategy", "venue": "coinbase",
                         "symbol": "BTC/USDT", "side": "buy", "order_type": "market", "qty": 1.,
                         "status": "submitted", "linked_order_id": "o1", "client_order_id": "i1", "meta": {}})
    intent_reconciler.reconcile_once(qdb=queue, pdb=paper, jdb=journal)
    intent_reconciler.reconcile_once(qdb=queue, pdb=paper, jdb=journal)  # retry must not duplicate/upgrade
    assert journal.count() == 1
    return journal.list_fills()[0]["execution_identity_evidence"]


def verified(meta):
    return {**{k: meta[k] for k in ("execution_identity", "execution_identity_sha256")},
            "execution_identity_fill_status": "cost_policy_verified"}


def test_matching_stored_evidence_marks_fill_verified(stores):
    meta = identity()
    ev = run(stores, order_meta=meta, fill_evidence=verified(meta))
    assert ev["fill_cost_policy_verified"] is True
    assert ev["journal_identity_status"] == "fill_cost_policy_verified"
    assert ev["fill_evidence_status"] == "cost_policy_verified"


def test_missing_stored_evidence_stays_order_policy_only(stores):
    ev = run(stores, order_meta=identity(), fill_evidence=None)
    assert ev["fill_cost_policy_verified"] is False and ev["journal_identity_status"] == "order_policy_only"
    assert ev["fill_evidence_status"] == "missing_fill_evidence"


@pytest.mark.parametrize("field,value", [("version", True), ("sma_period", 200.0)])
def test_equal_but_noncanonical_stored_identity_never_verifies(stores, field, value):
    meta = identity()
    evidence = copy.deepcopy(verified(meta))
    payload = evidence["execution_identity"]
    if field == "version":
        payload[field] = value
    else:
        payload["parameters"][field] = value
    assert payload == meta["execution_identity"]
    ev = run(stores, order_meta=meta, fill_evidence=evidence)
    assert ev["fill_cost_policy_verified"] is False
    assert ev["journal_identity_status"] == "order_policy_only"
    assert ev["fill_evidence_status"] == "invalid_fill_evidence"


@pytest.mark.parametrize("mutate,expected", [
    (lambda e: {**e, "execution_identity_sha256": "c" * 64}, "fill_evidence_identity_mismatch"),
    (lambda e: {"execution_identity_fill_status": "invalid", "execution_identity_fill_error_type": "ValueError"},
     "invalid_fill_evidence"),
    (lambda e: {**e, "execution_identity_fill_status": "something_else"}, "invalid_fill_evidence"),
])
def test_unverifiable_stored_evidence_never_verifies(stores, mutate, expected):
    meta = identity()
    ev = run(stores, order_meta=meta, fill_evidence=mutate(verified(meta)))
    assert ev["fill_cost_policy_verified"] is False and ev["fill_evidence_status"] == expected


def test_corrupt_paper_storage_never_verifies(stores):
    meta = identity()
    ev = run(stores, order_meta=meta, fill_evidence=verified(meta), corrupt=True)
    assert ev["fill_cost_policy_verified"] is False and ev["fill_evidence_status"] == "invalid_storage"


def test_invalid_order_identity_cannot_be_rescued_by_fill_evidence(stores):
    meta = identity()
    good = verified(meta)
    meta = {**meta, "execution_identity_sha256": "b" * 64}
    ev = run(stores, order_meta=meta, fill_evidence=good)
    assert ev["journal_identity_status"] == "invalid" and ev["fill_cost_policy_verified"] is False


def test_store_without_getter_is_missing_not_verified():
    meta = identity()
    extra = intent_reconciler._journal_identity_extra(
        {"meta": meta, "venue": "coinbase", "symbol": "BTC/USDT"},
        intent_reconciler._stored_fill_evidence(object(), "f1"))
    assert extra["execution_identity_evidence"]["fill_cost_policy_verified"] is False
    assert extra["execution_identity_evidence"]["fill_evidence_status"] == "missing_fill_evidence"


def test_engine_produced_evidence_round_trips_to_verified_journal(stores):
    from services.execution import paper_engine
    meta = identity()
    produced = paper_engine._fill_identity_extra(
        {"meta": meta, "venue": "coinbase", "symbol": "BTC/USDT"},
        {"fee_bps": 7.5, "slippage_bps": 5.0, "quote_currency": "USDT"})
    assert produced["execution_identity_fill_status"] == "cost_policy_verified"
    ev = run(stores, order_meta=meta, fill_evidence=produced)
    assert ev["fill_cost_policy_verified"] is True


def test_engine_cost_mismatch_round_trips_to_unverified_journal(stores):
    from services.execution import paper_engine
    meta = identity()
    produced = paper_engine._fill_identity_extra(
        {"meta": meta, "venue": "coinbase", "symbol": "BTC/USDT"},
        {"fee_bps": 50.0, "slippage_bps": 5.0, "quote_currency": "USDT"})
    ev = run(stores, order_meta=meta, fill_evidence=produced)
    assert ev["fill_cost_policy_verified"] is False and ev["fill_evidence_status"] == "invalid_fill_evidence"
