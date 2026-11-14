"""Fresh-only currency initialization; no real accounts, inputs or configuration."""
from concurrent.futures import ThreadPoolExecutor
import json
import threading

import pytest

from tests.test_paper_account_snapshot import db, state_rows, seed_order
from docs.review_artifacts.paper_profile_candidate_20261114.test_profiles import (
    PROFILES, isolated, load_candidate, market_inputs,
)


@pytest.mark.parametrize("currency,expected", [(" usd ", "USD"), ("eur", "EUR"), ("USDT", "USDT")])
def test_fresh_currency_is_immediately_available_to_cash_reader(db, currency, expected):
    assert db.initialize_account(1000, currency) == {"baseline_created": True}
    assert db.entry_cash_snapshot() == {
        "cash_quote": "1000.0", "quote_currency": expected, "nonflat_positions": 0, "open_orders": 0}
    assert json.loads(db.get_state("paper_account_origin_v1"))["quote_currency"] == expected
    before = state_rows()
    assert db.initialize_account(5000, "OTHER") == {"baseline_created": False}
    assert state_rows() == before


@pytest.mark.parametrize("currency", ["EUR", "USD", "", "not/known"])
def test_existing_currency_without_cash_is_not_reinterpreted_as_fresh(db, currency):
    db.set_state("quote_currency", currency)
    assert db.initialize_account(1000, "USD") == {"baseline_created": False}
    assert db.get_state("quote_currency") == currency
    assert db.get_state("paper_account_origin_v1") is None


@pytest.mark.parametrize("history", ["cash", "order", "origin", "position", "equity"])
def test_legacy_missing_currency_is_not_inferred_from_new_configuration(db, history):
    if history == "cash":
        db.set_state("cash_quote", "725.123")
    elif history == "order":
        seed_order(db)
    elif history == "origin":
        db.set_state("paper_account_origin_v1", '{"quote_currency":"EUR"}')
    elif history == "equity":
        db.insert_equity("old", 10, 10, 0, 0)
    else:
        db.upsert_position("BTC/USD", 0, 0, 0)
    before = state_rows()
    assert db.initialize_account(1000, "USD") == {"baseline_created": False}
    assert db.get_state("quote_currency") is None
    for key, value in before.items():
        assert db.get_state(key) == value
    with pytest.raises(KeyError, match="quote_currency"):
        db.entry_cash_snapshot()
    if history == "equity":
        assert db.list_equity() == [{"ts": "old", "cash_quote": 10, "equity_quote": 10,
                                     "unrealized_pnl": 0, "realized_pnl": 0}]


@pytest.mark.parametrize("failed_key", ["quote_currency", "paper_account_origin_v1"])
def test_currency_and_origin_write_failure_rolls_back_every_new_field(db, monkeypatch, failed_key):
    original = db._set_state_conn

    def fail(con, key, value):
        original(con, key, value)
        if key == failed_key:
            raise RuntimeError("synthetic initialization write failure")

    monkeypatch.setattr(db, "_set_state_conn", fail)
    with pytest.raises(RuntimeError, match="synthetic initialization"):
        db.initialize_account(1000, "USD")
    assert state_rows() == {}


def test_concurrent_initializers_bind_cash_currency_and_origin_to_one_winner(db):
    barrier = threading.Barrier(3)

    def initialize(values):
        barrier.wait(timeout=3)
        return db.initialize_account(*values)

    with ThreadPoolExecutor(max_workers=3) as pool:
        receipts = list(pool.map(initialize, [(1000, "USD"), (2000, "EUR"), (3000, "USDT")]))
    assert sum(result["baseline_created"] for result in receipts) == 1
    origin = json.loads(db.get_state("paper_account_origin_v1"))
    snapshot = db.entry_cash_snapshot()
    assert (float(snapshot["cash_quote"]), snapshot["quote_currency"]) in {
        (1000, "USD"), (2000, "EUR"), (3000, "USDT")}
    assert snapshot["quote_currency"] == origin["quote_currency"]
    assert float(snapshot["cash_quote"]) == origin["cash_quote"]


@pytest.mark.parametrize("profile", PROFILES, ids=lambda path: path.stem)
def test_nine_fresh_profiles_size_without_manually_seeding_currency(isolated, profile):
    _, _, _, _, engine, _, queue = isolated
    _, cfg, _ = load_candidate(isolated, profile)
    now, _, _ = market_inputs(isolated, cfg["symbol"])
    eng = engine.PaperEngine(clock=lambda: now.isoformat())
    from services.execution.paper_cash_entry import size_paper_entry
    sized = size_paper_entry(cfg=cfg, qdb=queue.IntentQueueSQLite(), pdb=eng.db,
                             venue="coinbase", symbol=cfg["symbol"], now=now.isoformat())
    assert sized["ok"], sized
    assert sized["qty"] * 101 * 1.005 <= 1000
    assert eng.db.get_state("quote_currency") == "USD"
    eng.set_cash_quote(725.123)
    restarted = engine.PaperEngine(clock=lambda: now.isoformat())
    assert restarted.cash_quote() == 725.123
    again = size_paper_entry(cfg=cfg, qdb=queue.IntentQueueSQLite(), pdb=restarted.db,
                             venue="coinbase", symbol=cfg["symbol"], now=now.isoformat())
    assert again["ok"] and float(again["evidence"]["cash"]) == 725.123
