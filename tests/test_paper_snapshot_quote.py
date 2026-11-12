"""Synthetic snapshot, real paper accounting and pending-exit integration."""
import ast
from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path
import sqlite3

import pytest

from services.market_data import tick_reader
from services.market_data.paper_snapshot_quote import assess_paper_quote, observe_paper_quote, read_paper_quote
from tests.test_hourly_candle_quality import NOW, market
from tests.test_pending_paper_exit_integration import harness, pending

VENUE = "coinbase"
SYMBOL = "ADA/USD"
NOW_MS = int(NOW.timestamp() * 1000)


def quote(symbol=SYMBOL, **fields):
    return {"venue": VENUE, "symbol": symbol, "symbol_mapped": symbol, "source": "public_ticker",
            "ticker_symbol": symbol,
            "bid": 99, "ask": 101, "last": 500, "ts_ms": NOW_MS, "exchange_ts_ms": 0, **fields}


def snapshot(path, *ticks, root_ms=NOW_MS):
    path.write_text(json.dumps({"ts_ms": root_ms, "ticks": list(ticks)}))


@pytest.fixture
def guarded(market, tmp_path, monkeypatch):
    path = tmp_path / "public_status.json"
    monkeypatch.setattr(tick_reader, "LATEST", path)
    market.eng.cfg.update(require_fresh_hourly_candles=False, require_fresh_snapshot_quotes=True)
    original = os.environ.get("CBP_QUOTE_BEFORE_ENGINE")
    if original:
        source = Path(original).read_bytes()
        assert hashlib.sha256(source).hexdigest() == "757b798272cd95993e0e57b174d6277806188fcb3263387f12a77f375870328e"
        import services.execution.paper_engine as module

        cls = next(node for node in ast.parse(source).body
                   if isinstance(node, ast.ClassDef) and node.name == "PaperEngine")
        for name in ("_pre_submit_gate", "_apply_fill", "evaluate_open_orders"):
            method = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == name)
            namespace = {}
            exec(compile(ast.Module(body=[method], type_ignores=[]), original, "exec"), vars(module), namespace)
            monkeypatch.setattr(module.PaperEngine, name, namespace[name])
    snapshot(path, quote())
    return market, path


def submit(eng, *, client="test", side="buy", order_type="market", limit=None, created=None):
    return eng.submit_order(client_order_id=client, venue=VENUE, symbol=SYMBOL, side=side,
                            order_type=order_type, qty=1, limit_price=limit, intent_created_ts=created)


def test_wrong_ticker_return_cannot_price_a_paper_sell(guarded, monkeypatch):
    from services.market_data import system_status_publisher as publisher

    rig, path = guarded
    rig.eng.db.upsert_position(SYMBOL, 1, 90, 0)
    assert submit(rig.eng, side="sell")["ok"]

    class Adapter:
        id = VENUE

        def fetch_ticker(self, symbol):
            assert symbol == SYMBOL
            return {"symbol": "BTC/USD", "bid": 999, "ask": 1001, "last": 1000}

    monkeypatch.setattr(publisher, "_symbols", lambda: [SYMBOL])
    monkeypatch.setattr(publisher, "_use_sample_ohlcv_ticks", lambda: False)
    monkeypatch.setenv("CBP_COMPONENT_VENUE", VENUE)
    monkeypatch.setattr(publisher, "map_symbol", lambda venue, symbol: symbol)
    monkeypatch.setattr(publisher, "make_exchange", lambda *args, **kwargs: Adapter())
    monkeypatch.setattr(publisher.time, "time", lambda: NOW.timestamp())
    path.write_text(json.dumps(publisher.fetch_status()))
    assert rig.eng.evaluate_open_orders()["filled"] == 0
    assert not rig.eng.db.list_fills()
    assert rig.eng.db.get_position(SYMBOL)["qty"] == 1


def test_direct_fill_cannot_bypass_canonical_buy_limit(guarded):
    rig, _ = guarded
    assert submit(rig.eng, order_type="limit", limit=100)["ok"]
    assert rig.eng.evaluate_open_orders()["filled"] == 0
    order = rig.eng.db.get_order_by_client_id("test")
    # A caller cannot replace the stored order with more permissive parameters.
    order.update(order_type="market", limit_price=200)
    evidence, _ = read_paper_quote(VENUE, SYMBOL, clock=rig.clock)
    result = rig.eng._apply_fill(order, 102.0, 1.0, quote_evidence=evidence)
    assert result == {"ok": False, "reason": "quote_data:price_model_mismatch", "unresolved": True}
    assert not rig.eng.db.list_fills() and rig.eng.cash_quote() == 1000


def test_buy_retry_returns_only_the_committed_fill_identity(guarded):
    rig, _ = guarded
    assert submit(rig.eng)["ok"]
    order = rig.eng.db.get_order_by_client_id("test")
    assert rig.eng.evaluate_open_orders()["filled"] == 1
    stored, = rig.eng.db.list_fills()
    cash = rig.eng.cash_quote()
    retry = rig.eng._apply_fill(order, 103.0, 1.5)
    assert retry == {"ok": True, "idempotent": True, **{
        key: stored[key] for key in ("fill_id", "price", "qty", "fee")
    }}
    assert rig.eng.db.get_fill_quote_evidence(retry["fill_id"])["mid"] == 100
    assert rig.eng.db.list_fills() == [stored] and rig.eng.cash_quote() == cash


@pytest.mark.parametrize("damage", ["missing", "duplicate"])
def test_buy_retry_fails_explicitly_on_missing_or_conflicting_ledger(guarded, damage):
    import storage.paper_trading_sqlite as ledger

    rig, _ = guarded
    assert submit(rig.eng)["ok"]
    order = rig.eng.db.get_order_by_client_id("test")
    assert rig.eng.evaluate_open_orders()["filled"] == 1
    cash = rig.eng.cash_quote()
    with sqlite3.connect(ledger.DB_PATH) as con:
        if damage == "missing":
            con.execute("DELETE FROM paper_fills")
        else:
            con.execute("INSERT INTO paper_fills SELECT 'conflict', order_id, ts, price, qty, fee, "
                        "fee_currency FROM paper_fills")
    fills = rig.eng.db.list_fills()
    assert rig.eng._apply_fill(order, 103.0, 1.5) == {
        "ok": False, "reason": "missing_or_conflicting_fill", "unresolved": True,
    }
    assert rig.eng.db.list_fills() == fills and rig.eng.cash_quote() == cash


def test_market_price_uses_configured_slippage_at_both_boundaries(guarded):
    rig, _ = guarded
    rig.eng.cfg["slippage_bps"] = 25
    assert submit(rig.eng)["ok"]
    order = rig.eng.db.get_order_by_client_id("test")
    evidence, _ = read_paper_quote(VENUE, SYMBOL, clock=rig.clock)
    assert rig.eng._apply_fill(order, 100.0, 1.0, quote_evidence=evidence)["reason"] == (
        "quote_data:price_model_mismatch"
    )
    assert rig.eng.evaluate_open_orders()["filled"] == 1
    assert rig.eng.db.list_fills()[0]["price"] == pytest.approx(100.25)


@pytest.mark.parametrize("age,ok", [(0, True), (5, True), (5.001, False), (-0.001, False)])
def test_quote_receipt_age_boundary(age, ok):
    result, reason = assess_paper_quote({**quote(), "snapshot_ts_ms": NOW_MS}, venue=VENUE,
                                       symbol=SYMBOL, now=NOW + timedelta(seconds=age))
    assert (result is not None) is ok
    assert (reason is None) is ok


@pytest.mark.parametrize("tick,root_ms,reason", [
    (quote("BTC/USD"), NOW_MS, "missing_quote"),
    (quote(venue="kraken"), NOW_MS, "missing_quote"),
    (quote(source=None), NOW_MS, "unverified_source"),
    (quote(ticker_symbol=None), NOW_MS, "unverified_ticker_symbol"),
    (quote(ticker_symbol="BTC/USD"), NOW_MS, "unverified_ticker_symbol"),
    (quote(source="sample_ohlcv"), NOW_MS, "unverified_source"),
    (quote(bid=None), NOW_MS, "invalid_book"),
    (quote(bid=True), NOW_MS, "invalid_book"),
    (quote(bid=0), NOW_MS, "invalid_book"),
    (quote(ask=98), NOW_MS, "invalid_book"),
    (quote(ts_ms=NOW_MS - 1), NOW_MS, "invalid_timestamp"),
    (quote(ts_ms=NOW_MS + 1), NOW_MS, "future_quote"),
    (quote(), NOW_MS - 5001, "stale_quote"),
    (quote(ts_ms=NOW_MS - 5001), NOW_MS - 5002, "stale_quote"),
])
def test_guard_refuses_invalid_snapshot_before_submission(guarded, tick, root_ms, reason):
    rig, path = guarded
    snapshot(path, tick, root_ms=root_ms)
    assert submit(rig.eng) == {"ok": False, "reason": "quote_data:" + reason}
    assert not rig.eng.db.list_orders() and not rig.eng.db.list_fills()


@pytest.mark.parametrize("kind,reason", [("missing", "snapshot_unreadable"), ("duplicate", "ambiguous_quote"),
    ("nonfinite", "invalid_snapshot"), ("oversized", "invalid_snapshot"), ("duplicate_key", "invalid_snapshot")])
def test_guarded_reader_rejects_ambiguous_or_unreadable_snapshot(guarded, kind, reason):
    rig, path = guarded
    if kind == "missing":
        path.unlink()
    elif kind == "duplicate":
        snapshot(path, quote(), quote("ada-usd"))
    elif kind == "nonfinite":
        snapshot(path, quote(ask=float("inf")))
    elif kind == "duplicate_key":
        path.write_text('{"ticks":[],"ticks":[]}')
    else:
        path.write_bytes(b" " * 1_048_577)
    assert read_paper_quote(VENUE, SYMBOL, clock=rig.clock) == (None, reason)


def test_unavailable_clock_and_malformed_policy_fail_closed(guarded):
    rig, _ = guarded

    def broken_clock():
        raise RuntimeError("synthetic clock unavailable")

    assert read_paper_quote(VENUE, SYMBOL, clock=broken_clock) == (None, "invalid_clock")
    rig.eng.cfg["require_fresh_snapshot_quotes"] = "false"
    assert submit(rig.eng) == {"ok": False, "reason": "quote_data:invalid_policy"}


def test_optional_observer_does_not_block_on_non_regular_snapshot(guarded):
    rig, path = guarded
    path.unlink()
    os.mkfifo(path)
    result = observe_paper_quote(VENUE, SYMBOL, clock=rig.clock)
    assert result["reason"] == "invalid_snapshot" and not result["ok"]
    assert result["bid_present"] is None and result["quote_age_ms"] is None


@pytest.mark.parametrize("side,order_type,limit,expected", [
    ("buy", "market", None, 100), ("sell", "market", None, 100),
    ("buy", "limit", 102, 101), ("sell", "limit", 98, 99),
])
def test_fill_commits_exact_quote_evidence_without_changing_price_model(guarded, side, order_type, limit, expected):
    rig, _ = guarded
    if side == "sell":
        rig.eng.db.upsert_position(SYMBOL, 1, 90, 0)
    assert submit(rig.eng, side=side, order_type=order_type, limit=limit)["ok"]
    assert rig.eng.evaluate_open_orders()["filled"] == 1
    fill, = rig.eng.db.list_fills()
    assert fill["price"] == expected
    evidence = rig.eng.db.get_fill_quote_evidence(fill["fill_id"])
    assert evidence == {"version": 1, "venue": VENUE, "symbol": SYMBOL, "symbol_mapped": SYMBOL,
                        "ticker_symbol": SYMBOL,
                        "source": "public_ticker", "bid": 99, "ask": 101, "mid": 100,
                        "ts_ms": NOW_MS, "snapshot_ts_ms": NOW_MS, "exchange_ts_ms": None}
    assert rig.eng.evaluate_open_orders()["filled"] == 0
    assert rig.eng.db.get_fill_quote_evidence(fill["fill_id"]) == evidence


def test_resting_buy_stays_open_without_fresh_quote_until_ttl(guarded):
    rig, path = guarded
    assert submit(rig.eng)["ok"]
    rig.now[0] += timedelta(seconds=6)
    result = rig.eng.evaluate_open_orders()
    assert result["filled"] == result["rejected"] == 0
    assert result["details_sample"][0]["result"]["reason"] == "quote_data:stale_quote"
    assert rig.eng.db.get_order_by_client_id("test")["status"] == "new"
    rig.now[0] += timedelta(seconds=114)
    snapshot(path, quote(ts_ms=NOW_MS + 120000), root_ms=NOW_MS + 120000)
    assert rig.eng.evaluate_open_orders()["filled"] == 0
    assert rig.eng.db.get_order_by_client_id("test")["status"] == "expired"
    assert not rig.eng.db.list_fills() and rig.eng.cash_quote() == 1000


@pytest.mark.parametrize("fault", ["evidence_insert", "quote_deadline", "buy_deadline", "wrong_market",
                                  "invalid_accounting"])
def test_serialized_guard_rolls_back_without_fill_or_evidence(guarded, monkeypatch, fault):
    rig, _ = guarded
    created = (NOW - timedelta(seconds=119)).isoformat() if fault == "buy_deadline" else None
    assert submit(rig.eng, created=created)["ok"]
    order = rig.eng.db.get_order_by_client_id("test")
    received = {**quote(symbol="BTC/USD" if fault == "wrong_market" else SYMBOL), "snapshot_ts_ms": NOW_MS}
    import storage.paper_trading_sqlite as ledger

    if fault == "invalid_accounting":
        rig.eng.db.set_state("realized_pnl", "nan")
    if fault == "evidence_insert":
        with sqlite3.connect(ledger.DB_PATH) as con:
            con.execute("""CREATE TRIGGER break_evidence BEFORE INSERT ON paper_state
                WHEN NEW.k GLOB 'paper_fill_quote:*'
                BEGIN SELECT RAISE(ABORT, 'fixture'); END""")
    elif fault in {"quote_deadline", "buy_deadline"}:
        original = rig.eng.db._insert_fill_conn

        def delay(con, row):
            inserted = original(con, row)
            rig.now[0] += timedelta(seconds=6 if fault == "quote_deadline" else 2)
            return inserted

        monkeypatch.setattr(rig.eng.db, "_insert_fill_conn", delay)
    result = rig.eng._apply_fill(order, 100.0, 1.0, quote_evidence=received)
    assert result == {"ok": False, "unresolved": True, "reason": {
        "evidence_insert": "quote_data:evidence_unwritable", "quote_deadline": "quote_data:stale_quote",
        "buy_deadline": "paper_buy_ttl:expired", "wrong_market": "quote_data:wrong_market",
        "invalid_accounting": "quote_data:invalid_accounting",
    }[fault]}
    assert not rig.eng.db.list_fills() and rig.eng.cash_quote() == 1000
    assert rig.eng.db.get_position(SYMBOL) is None
    assert rig.eng.db.get_order_by_client_id("test")["status"] == "new"
    with sqlite3.connect(ledger.DB_PATH) as con:
        assert not con.execute("SELECT k FROM paper_state WHERE k GLOB 'paper_fill_quote:*'").fetchall()


def test_pending_exit_waits_for_fresh_snapshot_then_fills_once(pending, monkeypatch, tmp_path):
    f = pending
    f.eng.cfg["require_fresh_snapshot_quotes"] = True
    f.eng._clock = lambda: NOW.isoformat()
    path = tmp_path / "status.json"
    monkeypatch.setattr(tick_reader, "LATEST", path)
    root = f.trigger()
    snapshot(path, quote(root["symbol"], bid=95, ask=97))
    assert f.consume()["submitted"] == 1
    snapshot(path, quote(root["symbol"], ts_ms=NOW_MS - 6000), root_ms=NOW_MS - 6000)
    assert f.eng.evaluate_open_orders()["filled"] == 0
    f.reconcile()
    assert not f.root_fills(root)
    assert f.root(root)["status"] not in {"filled", "rejected", "superseded"}
    snapshot(path, quote(root["symbol"], bid=95, ask=97))
    assert f.eng.evaluate_open_orders()["filled"] == 1
    f.reconcile()
    assert f.root(root)["status"] == "filled"
    fill, = f.root_fills(root)
    assert f.eng.db.get_fill_quote_evidence(fill["fill_id"])["mid"] == fill["price"] == 96
    assert f.eng.evaluate_open_orders()["filled"] == 0


def test_legacy_profile_never_backfills_quote_evidence(guarded):
    rig, path = guarded
    rig.eng.cfg.pop("require_fresh_snapshot_quotes")
    path.unlink()
    assert submit(rig.eng)["ok"]
    assert rig.eng.evaluate_open_orders()["filled"] == 1
    fill, = rig.eng.db.list_fills()
    assert rig.eng.db.get_fill_quote_evidence(fill["fill_id"]) is None
