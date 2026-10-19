import sqlite3

import pytest

from services.execution import intent_reconciler
from services.strategies.execution_identity import identity_evidence
from storage import intent_queue_sqlite, paper_trading_sqlite, trade_journal_sqlite


def identity():
    return identity_evidence({
        "version": 1, "cohort_id": "synthetic-only", "strategy_name": "sma_200_trend",
        "parameters": {"sma_period": 200}, "entry_policy": {"rule": "synthetic"},
        "exit_policy": {"stop": 0}, "sizing": {"qty": 1},
        "costs": {"fee_bps": 7.5, "slippage_bps": 5., "quote_currency": "USDT",
                  "basis_version": "paper_fee_inclusive_average_v1"},
        "market": {"venue": "coinbase", "symbol": "BTC/USDT", "timeframe": "1d",
                   "source": "public_ohlcv", "sample_mode": False},
        "implementation": {key: "a"*64 for key in ("signal", "resolver", "exits", "paper_engine")},
    })


@pytest.fixture
def journal(monkeypatch, tmp_path):
    monkeypatch.setattr(trade_journal_sqlite, "DB_PATH", tmp_path/"journal.sqlite")
    return trade_journal_sqlite.TradeJournalSQLite()


def row():
    return {"fill_id":"f1", "order_id":"o1", "fill_ts":"2026-10-08T12:00:00Z",
            "venue":"coinbase", "symbol":"BTC/USDT", "side":"buy", "qty":1.,
            "price":100., "fee":.075, "fee_currency":"USDT"}


def test_journal_preserves_first_evidence_without_retroactive_upgrade(journal):
    fill = row()
    journal.insert_fill(fill)
    fill["execution_identity_evidence"] = {"journal_identity_status":"order_policy_only"}
    journal.insert_fill(fill)
    assert journal.count() == 1
    assert "execution_identity_evidence" not in journal.list_fills()[0]
    fill["fill_id"] = "f2"
    journal.insert_fill(fill)
    fill["execution_identity_evidence"] = {"journal_identity_status":"different"}
    journal.insert_fill(fill)
    stored = {r["fill_id"]: r for r in journal.list_fills()}
    assert stored["f2"]["execution_identity_evidence"]["journal_identity_status"] == "order_policy_only"


def test_fill_and_identity_insert_are_atomic(journal):
    fill = row()
    fill["execution_identity_evidence"] = {"bad":float("nan")}
    with pytest.raises(ValueError):
        journal.insert_fill(fill)
    assert journal.count() == 0


def test_existing_schema_and_rows_are_preserved(monkeypatch, tmp_path):
    path = tmp_path/"legacy.sqlite"
    monkeypatch.setattr(trade_journal_sqlite, "DB_PATH", path)
    with sqlite3.connect(path) as con:
        con.executescript(trade_journal_sqlite.SCHEMA.split("CREATE TABLE IF NOT EXISTS journal_fill_identity")[0])
        con.execute("INSERT INTO journal_fills(fill_id,journal_ts,order_id,fill_ts,venue,symbol,side,qty,price,fee,fee_currency) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    ("old", "old-ts", "old-order", "old-ts", "coinbase", "BTC/USDT", "buy", 1., 100., .075, "USDT"))
    store = trade_journal_sqlite.TradeJournalSQLite()
    assert store.count() == 1
    assert store.list_fills()[0]["fill_id"] == "old"
    assert "execution_identity_evidence" not in store.list_fills()[0]


def test_corrupt_sidecar_is_not_valid_evidence(journal):
    fill = row()
    fill["execution_identity_evidence"] = {}
    journal.insert_fill(fill)
    with sqlite3.connect(trade_journal_sqlite.DB_PATH) as con:
        con.execute("UPDATE journal_fill_identity SET evidence_json='broken'")
    assert journal.list_fills()[0]["execution_identity_evidence"] == {"journal_identity_status":"invalid_storage"}


@pytest.mark.parametrize("mode", ["matching", "mismatch", "legacy"])
def test_real_paper_queue_fill_to_journal(monkeypatch, tmp_path, journal, mode):
    monkeypatch.setattr(intent_queue_sqlite, "DB_PATH", tmp_path/"queue.sqlite")
    monkeypatch.setattr(paper_trading_sqlite, "DB_PATH", tmp_path/"paper.sqlite")
    monkeypatch.setattr(intent_reconciler, "log_strategy_outcome", lambda row: None)
    queue = intent_queue_sqlite.IntentQueueSQLite()
    paper = paper_trading_sqlite.PaperTradingSQLite()
    meta = identity() if mode != "legacy" else {}
    if mode == "mismatch":
        meta["execution_identity_sha256"] = "b"*64
    order = {"order_id":"o1", "client_order_id":"i1", "ts":"2026-10-08T12:00:00Z",
             "venue":"coinbase", "symbol":"BTC/USDT", "side":"buy",
             "order_type":"market", "qty":1., "status":"new", "meta":meta}
    paper.insert_order(order)
    paper.set_state("cash_quote", "1000")
    assert paper.apply_fill(order=order, ts=order["ts"], price=100., qty=1., fee=.075,
                            fee_currency="USDT")["ok"]
    queue.upsert_intent({"intent_id":"i1", "ts":order["ts"], "source":"strategy",
                        "venue":order["venue"], "symbol":order["symbol"], "side":"buy",
                        "order_type":"market", "qty":1., "status":"submitted",
                        "linked_order_id":"o1", "client_order_id":"i1", "meta":{}})
    intent_reconciler.reconcile_once(qdb=queue, pdb=paper, jdb=journal)
    assert queue.get_intent("i1")["status"] == "filled"
    stored = journal.list_fills()[0]
    assert stored["fee"] == .075
    if mode == "legacy":
        assert "execution_identity_evidence" not in stored
    else:
        evidence = stored["execution_identity_evidence"]
        assert evidence["fill_cost_policy_verified"] is False
        assert evidence["journal_identity_status"] == ("order_policy_only" if mode == "matching" else "invalid")
    intent_reconciler.reconcile_once(qdb=queue, pdb=paper, jdb=journal)
    assert journal.count() == 1
