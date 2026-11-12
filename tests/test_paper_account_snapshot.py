from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import gc
import json
import sqlite3
import threading

import pytest

from storage import paper_trading_sqlite as store


@pytest.fixture
def db(monkeypatch, tmp_path):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "paper.sqlite")
    return store.PaperTradingSQLite()


def queue_db():
    path = store.DB_PATH.parent / "intent_queue.sqlite"
    with closing(sqlite3.connect(path)) as con, con:
        con.execute("PRAGMA journal_mode=WAL")
        con.executescript("""
            CREATE TABLE trade_intents (
                intent_id TEXT PRIMARY KEY, created_ts TEXT, updated_ts TEXT, source TEXT,
                venue TEXT, symbol TEXT, side TEXT, order_type TEXT, qty REAL, status TEXT,
                client_order_id TEXT, linked_order_id TEXT, meta TEXT, last_error TEXT);
            CREATE TABLE paper_buy_events (intent_id TEXT, reason TEXT);
            CREATE TABLE paper_exit_events (intent_id TEXT, reason TEXT);
        """)
    return path


def seed_order(db):
    db.insert_order(dict(order_id="order", client_order_id="direct", ts="2026-11-03T00:00:00Z",
                         venue="coinbase", symbol="BTC/USD", side="buy", order_type="market",
                         qty=1, status="new", strategy_id="test", meta={"omitted": "private"}))


def test_queue_fixture_closes_writer_before_byte_preservation_check(db, monkeypatch):
    original_connect = sqlite3.connect
    opened = []

    class FixtureConnection(sqlite3.Connection):
        closed = False

        def close(self):
            self.closed = True
            super().close()

    def connect(*args, **kwargs):
        con = original_connect(*args, factory=FixtureConnection, **kwargs)
        opened.append(con)
        return con

    monkeypatch.setattr(sqlite3, "connect", connect)
    path = queue_db()
    assert len(opened) == 1 and opened[0].closed
    before = path.read_bytes()
    gc.collect()
    assert path.read_bytes() == before


def state_rows():
    with sqlite3.connect(store.DB_PATH) as con:
        return dict(con.execute("SELECT k,v FROM paper_state"))


def test_initialize_fresh_origin_and_defaults_are_atomic_and_not_rebased(db):
    assert db.initialize_account(1000, " usd ") == {"baseline_created": True}
    origin = json.loads(db.get_state("paper_account_origin_v1"))
    assert origin == {"schema": 1, "cash_quote": 1000.0, "quote_currency": "USD"}
    assert db.get_state("cash_quote") == "1000.0"
    assert db.get_state("realized_pnl") == "0.0"
    before = state_rows()
    assert db.initialize_account(5000, "EUR") == {"baseline_created": False}
    assert state_rows() == before


@pytest.mark.parametrize("cash", [True, None, "bad", 0, -1, float("nan"), float("inf"), 10 ** 1000])
def test_invalid_initial_cash_writes_nothing(db, cash):
    with pytest.raises(ValueError, match="invalid_starting_cash_quote"):
        db.initialize_account(cash, "USD")
    assert state_rows() == {}


@pytest.mark.parametrize("currency", [None, 42, "", " ", "USD/BTC", "US D", "\u20ac"])
def test_invalid_initial_quote_writes_nothing(db, currency):
    with pytest.raises(ValueError, match="invalid_quote_currency"):
        db.initialize_account(1000, currency)
    assert state_rows() == {}


@pytest.mark.parametrize("cash,realized", [("725.123", "12.5"), ("0", None), ("broken", "bad")])
def test_existing_cash_never_changes_or_acquires_inferred_origin(db, cash, realized):
    db.set_state("cash_quote", cash)
    if realized is not None:
        db.set_state("realized_pnl", realized)
    assert not db.initialize_account(1000, "USD")["baseline_created"]
    assert db.get_state("cash_quote") == cash
    assert db.get_state("realized_pnl") == (realized if realized is not None else "0.0")
    assert db.get_state("paper_account_origin_v1") is None


@pytest.mark.parametrize("origin", [None, '{"schema":1,"cash_quote":1000,"quote_currency":"USD"}'])
@pytest.mark.parametrize("unused_cash,unused_quote", [(0, "bad/quote"), ("not-a-number", None)])
def test_existing_cash_ignores_unused_invalid_defaults_and_still_initializes_realized(db, origin, unused_cash, unused_quote):
    db.set_state("cash_quote", "725.123")
    if origin is not None:
        db.set_state("paper_account_origin_v1", origin)
    assert db.initialize_account(unused_cash, unused_quote) == {"baseline_created": False}
    assert db.get_state("cash_quote") == "725.123"
    assert db.get_state("realized_pnl") == "0.0"
    assert db.get_state("paper_account_origin_v1") == origin


def test_legacy_missing_cash_does_not_validate_unused_quote_or_infer_origin(db):
    seed_order(db)
    assert db.initialize_account(1000, None) == {"baseline_created": False}
    assert db.get_state("cash_quote") == "1000.0"
    assert db.get_state("realized_pnl") == "0.0"
    assert db.get_state("paper_account_origin_v1") is None


@pytest.mark.parametrize("evidence", ["order", "fill", "zero_position", "realized", "tiny_realized", "bad_realized", "origin"])
def test_legacy_data_never_gets_a_baseline_but_retains_existing_default_behavior(db, evidence):
    if evidence == "order":
        seed_order(db)
    elif evidence == "fill":
        db.insert_fill(dict(fill_id="orphan", order_id="missing", ts="old", price=100, qty=1, fee=1, fee_currency="USD"))
    elif evidence == "zero_position":
        db.upsert_position("BTC/USD", 0, 0, 0)
    elif evidence in {"realized", "tiny_realized", "bad_realized"}:
        db.set_state("realized_pnl", {"realized": "12", "tiny_realized": "1e-9999", "bad_realized": "NaN"}[evidence])
    else:
        db.set_state("paper_account_origin_v1", "preserve-old-origin")
    before = state_rows()
    assert not db.initialize_account(1000, "USD")["baseline_created"]
    assert db.get_state("cash_quote") == "1000.0"
    for key, value in before.items():
        assert db.get_state(key) == value
    assert db.get_state("paper_account_origin_v1") == before.get("paper_account_origin_v1")


@pytest.mark.parametrize("zero", ["0", "-0.0", "0e9999"])
def test_exact_existing_realized_zero_allows_fresh_origin(db, zero):
    db.set_state("realized_pnl", zero)
    assert db.initialize_account("1000", "USDT")["baseline_created"]
    assert db.get_state("realized_pnl") == zero


def test_initialization_failure_rolls_back_all_defaults_and_origin(db, monkeypatch):
    original = db._set_state_conn

    def fail(con, key, value):
        original(con, key, value)
        if key == "paper_account_origin_v1":
            raise RuntimeError("origin write failed")

    monkeypatch.setattr(db, "_set_state_conn", fail)
    with pytest.raises(RuntimeError, match="origin write failed"):
        db.initialize_account(1000, "USD")
    assert state_rows() == {}


def test_concurrent_initialization_has_one_origin_and_matching_cash(db):
    barrier = threading.Barrier(3)

    def initialize(cash):
        barrier.wait(timeout=3)
        return db.initialize_account(cash, "USD")

    with ThreadPoolExecutor(max_workers=3) as pool:
        receipts = list(pool.map(initialize, [1000, 2000, 3000]))
    assert sum(row["baseline_created"] for row in receipts) == 1
    origin = json.loads(db.get_state("paper_account_origin_v1"))
    assert origin["cash_quote"] == float(db.get_state("cash_quote"))


def test_snapshot_whitelists_all_rows_raw_state_and_fill_sequence(db):
    path = queue_db()
    with sqlite3.connect(path) as con:
        con.execute("INSERT INTO trade_intents VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    ("intent", "created", "updated", "strategy", "coinbase", "BTC/USD", "buy", "market",
                     1, "submitted", "direct", "order", "do-not-copy-meta", "do-not-copy-error"))
        con.executemany("INSERT INTO paper_buy_events VALUES(?,?)", [("deleted-buy", "private"), ("intent", "private")])
        con.executemany("INSERT INTO paper_exit_events VALUES(?,?)", [("deleted-sell", "private"), ("intent", "private")])
    db.initialize_account(1000, "USD")
    db.record_account_reconciliation_seen(["previous"])
    db.set_state("not_whitelisted", "do-not-copy-state")
    seed_order(db)
    with sqlite3.connect(store.DB_PATH) as con:
        con.execute("UPDATE paper_orders SET meta_json='not-json'")
    for fid, ts in [("z-first", "later"), ("a-second", "earlier")]:
        db.insert_fill(dict(fill_id=fid, order_id="order", ts=ts, price=100, qty=0.5, fee=1, fee_currency="USD"))
    db.upsert_position("BTC/USD", 1, 102, 0)
    db.upsert_position("ETH/USD", 0, 0, 3)
    before = state_rows()
    snapshot = db.account_reconciliation_snapshot()
    assert set(snapshot) == {"orders", "fills", "positions", "intents", "event_intent_ids", "state"}
    assert len(snapshot["orders"]) == 1 and "meta_json" not in snapshot["orders"][0]
    assert len(snapshot["orders"][0]) == 13
    assert [(row["sequence"], row["fill_id"]) for row in snapshot["fills"]] == [(1, "z-first"), (2, "a-second")]
    assert all(set(row) == {"sequence", "fill_id", "order_id", "ts", "price", "qty", "fee", "fee_currency"}
               for row in snapshot["fills"])
    assert len(snapshot["positions"]) == 2
    assert set(snapshot["intents"][0]) == {"intent_id", "created_ts", "updated_ts", "source", "venue", "symbol",
                                           "side", "order_type", "qty", "status", "client_order_id", "linked_order_id"}
    assert snapshot["event_intent_ids"] == ["deleted-buy", "deleted-sell", "intent"]
    assert set(snapshot["state"]) == {"cash_quote", "realized_pnl", "paper_account_origin_v1", "paper_watchdog_seen_v1"}
    assert all(isinstance(value, str) for value in snapshot["state"].values())
    assert state_rows() == before


@pytest.mark.parametrize("damage", ["missing", "events_missing", "corrupt"])
def test_snapshot_queue_errors_raise_without_creation_or_ledger_change(db, damage):
    path = store.DB_PATH.parent / "intent_queue.sqlite"
    if damage != "missing":
        queue_db()
        with sqlite3.connect(path) as con:
            if damage == "events_missing":
                con.execute("DROP TABLE paper_exit_events")
            else:
                con.execute("PRAGMA writable_schema=ON")
                con.execute("UPDATE sqlite_master SET sql='not sql' WHERE name='trade_intents'")
    db.initialize_account(1000, "USD")
    before = state_rows()
    with pytest.raises(sqlite3.Error):
        db.account_reconciliation_snapshot()
    assert path.exists() is (damage != "missing")
    assert state_rows() == before
    db.set_state("lock_released", "yes")


def test_snapshot_readonly_quoted_queue_opens_after_ledger_lock_and_closes_connections(db, monkeypatch):
    parent = store.DB_PATH.parent / "quoted #?% path"
    parent.mkdir()
    monkeypatch.setattr(store, "DB_PATH", parent / "paper.sqlite")
    isolated = store.PaperTradingSQLite()
    path = queue_db()
    before = path.read_bytes()
    original_connect = sqlite3.connect
    connections = []
    queue_queries = []

    class TrackedConnection(sqlite3.Connection):
        closed = False

        def close(self):
            self.closed = True
            super().close()

    def connect(database, *args, **kwargs):
        kwargs["factory"] = TrackedConnection
        if kwargs.get("uri"):
            assert str(database).endswith("?mode=ro") and "%23%3F%25" in str(database)
            assert kwargs["timeout"] == 0.25
            with original_connect(store.DB_PATH, timeout=0) as writer:
                with pytest.raises(sqlite3.OperationalError, match="locked"):
                    writer.execute("BEGIN IMMEDIATE")
        con = original_connect(database, *args, **kwargs)
        connections.append(con)
        if kwargs.get("uri"):
            with pytest.raises(sqlite3.OperationalError, match="readonly"):
                con.execute("DELETE FROM trade_intents")
            con.set_trace_callback(queue_queries.append)
        return con

    monkeypatch.setattr(sqlite3, "connect", connect)
    assert isolated.account_reconciliation_snapshot() == dict(
        orders=[], fills=[], positions=[], intents=[], event_intent_ids=[], state={})
    assert queue_queries[0] == "BEGIN" and queue_queries[-1] == "COMMIT"
    assert len(connections) == 2 and all(con.closed for con in connections)
    assert path.read_bytes() == before


def test_queue_inventory_and_event_ids_share_one_read_snapshot(db, monkeypatch):
    path = queue_db()
    original_connect = sqlite3.connect
    wrote = []

    def connect(database, *args, **kwargs):
        con = original_connect(database, *args, **kwargs)
        if kwargs.get("uri"):
            def trace(sql):
                if sql.startswith("SELECT intent_id FROM paper_buy_events") and not wrote:
                    with original_connect(path) as writer:
                        writer.execute("INSERT INTO trade_intents(intent_id) VALUES('later')")
                        writer.execute("INSERT INTO paper_buy_events(intent_id) VALUES('later')")
                    wrote.append(True)
            con.set_trace_callback(trace)
        return con

    monkeypatch.setattr(sqlite3, "connect", connect)
    first = db.account_reconciliation_snapshot()
    assert wrote and first["intents"] == [] and first["event_intent_ids"] == []
    second = db.account_reconciliation_snapshot()
    assert second["intents"][0]["intent_id"] == "later" and second["event_intent_ids"] == ["later"]


def test_snapshot_has_no_inventory_limits(db):
    path = queue_db()
    count = 2001
    with sqlite3.connect(path) as con:
        con.executemany("INSERT INTO trade_intents(intent_id) VALUES(?)", ((str(i),) for i in range(count)))
        con.executemany("INSERT INTO paper_buy_events(intent_id) VALUES(?)", ((str(i),) for i in range(count)))
    with sqlite3.connect(store.DB_PATH) as con:
        con.executemany("INSERT INTO paper_orders(order_id,client_order_id,created_ts,ts,venue,symbol,side,"
                        "order_type,qty,status) VALUES(?,?,'created','ts','venue','BTC/USD','buy','market',1,'new')",
                        ((str(i), str(i)) for i in range(count)))
        con.executemany("INSERT INTO paper_fills(fill_id,order_id,ts,price,qty,fee,fee_currency) "
                        "VALUES(?,?,'ts',100,1,1,'USD')", ((str(i), str(i)) for i in range(count)))
        con.executemany("INSERT INTO paper_positions VALUES(?,1,100,0,'ts')", ((str(i),) for i in range(count)))
    snapshot = db.account_reconciliation_snapshot()
    assert all(len(snapshot[key]) == count for key in ("orders", "fills", "positions", "intents", "event_intent_ids"))
    assert snapshot["fills"][-1]["sequence"] == count


@pytest.mark.parametrize("failure", ["queue_select", "queue_commit", "ledger_commit"])
def test_snapshot_failure_rolls_back_and_closes_both_connections(db, monkeypatch, failure):
    queue_db()
    db.initialize_account(1000, "USD")
    before = state_rows()
    original_connect = sqlite3.connect
    connections = []

    class FailingConnection(sqlite3.Connection):
        closed = False
        rolled_back = False
        is_queue = False

        def execute(self, sql, *args, **kwargs):
            if ((self.is_queue and failure == "queue_select" and sql.startswith("SELECT intent_id,created_ts"))
                    or (sql == "COMMIT" and ((self.is_queue and failure == "queue_commit")
                                            or (not self.is_queue and failure == "ledger_commit")))):
                raise sqlite3.OperationalError("snapshot injected failure")
            return super().execute(sql, *args, **kwargs)

        def rollback(self):
            self.rolled_back = True
            super().rollback()

        def close(self):
            self.closed = True
            super().close()

    def connect(database, *args, **kwargs):
        con = original_connect(database, *args, factory=FailingConnection, **kwargs)
        con.is_queue = bool(kwargs.get("uri"))
        connections.append(con)
        return con

    monkeypatch.setattr(sqlite3, "connect", connect)
    with pytest.raises(sqlite3.OperationalError, match="snapshot injected failure"):
        db.account_reconciliation_snapshot()
    assert len(connections) == 2 and all(con.closed and con.rolled_back for con in connections)
    assert state_rows() == before
    db.set_state("lock_released", "yes")


def test_seen_union_is_durable_deduplicated_and_changes_no_financial_state(db):
    db.initialize_account(1000, "USD")
    before = state_rows()
    assert db.record_account_reconciliation_seen(["b", "a", "a"]) == ["a", "b"]
    assert store.PaperTradingSQLite().record_account_reconciliation_seen(["c", "a"]) == ["a", "b", "c"]
    assert json.loads(db.get_state("paper_watchdog_seen_v1")) == ["a", "b", "c"]
    assert {key: value for key, value in state_rows().items() if key != "paper_watchdog_seen_v1"} == before


@pytest.mark.parametrize("raw", ["{", "null", "{}", '"id"', '[1]', '[""]', '[" id "]', '[NaN]'])
def test_malformed_prior_seen_is_never_replaced(db, raw):
    db.set_state("paper_watchdog_seen_v1", raw)
    with pytest.raises(ValueError, match="invalid_paper_watchdog_seen"):
        db.record_account_reconciliation_seen(["new"])
    assert db.get_state("paper_watchdog_seen_v1") == raw


@pytest.mark.parametrize("value", [None, "id", [1], [""], [" id "]])
def test_invalid_seen_input_writes_nothing(db, value):
    with pytest.raises(ValueError, match="invalid_account_reconciliation_intent_ids"):
        db.record_account_reconciliation_seen(value)
    assert state_rows() == {}


def test_seen_union_serializes_concurrent_updates(db):
    barrier = threading.Barrier(4)

    def record(index):
        barrier.wait(timeout=3)
        return db.record_account_reconciliation_seen(["intent-" + str(index)])

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(record, range(4)))
    assert json.loads(db.get_state("paper_watchdog_seen_v1")) == ["intent-" + str(i) for i in range(4)]


def test_seen_write_failure_rolls_back_union(db, monkeypatch):
    db.record_account_reconciliation_seen(["existing"])
    original = db._set_state_conn

    def fail(*args):
        original(*args)
        raise RuntimeError("seen write failed")

    monkeypatch.setattr(db, "_set_state_conn", fail)
    with pytest.raises(RuntimeError, match="seen write failed"):
        db.record_account_reconciliation_seen(["new"])
    assert json.loads(db.get_state("paper_watchdog_seen_v1")) == ["existing"]
