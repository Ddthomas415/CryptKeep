"""Independent-review probes for the spot-exit prototype: binary floating point in quantity checks.
Uses the package's own fixtures. Each probe asserts the behaviour a venue would produce a need for.

Run from an isolated copy of base 381bd477 with the prototype package extracted:
    PYTHONPATH=<isolated tree> python -m pytest -q -p no:cacheprovider probe_float_quantities.py
Result on 2026-10-07: 2 failed, 1 passed."""
import sqlite3
from storage.spot_exit_reservations import SpotExitReservations
from storage.execution_account_binding import ExecutionAccountBinding
from tests.test_execution_account_binding import CONTEXT
from tests.test_spot_exit_reservations import intent, terminal_setup


def _setup(tmp_path, held):
    path = tmp_path / "execution.sqlite"
    ExecutionAccountBinding(path).initialize(CONTEXT)
    with sqlite3.connect(path) as con:
        con.executescript(f"""
          CREATE TABLE live_positions(venue TEXT,symbol TEXT,qty REAL,updated_ts TEXT);
          INSERT INTO live_positions VALUES('coinbase','BTC/USD',{held!r},'v1');
          CREATE TABLE intents(intent_id TEXT PRIMARY KEY,exchange TEXT,symbol TEXT,side TEXT,qty REAL,mode TEXT,status TEXT);
        """)
    store = SpotExitReservations(path, account_context=CONTEXT)
    store.record_reconciliation(venue="coinbase", symbol="BTC/USD", evidence_id="recon1", exchange_qty=held, observed_ms=100, now_ms=100)
    return path, store


def test_two_exits_that_together_equal_the_holding_can_both_reserve(tmp_path):
    # Holding 0.3; exits of 0.1 and 0.2 are exactly the holding.
    path, s = _setup(tmp_path, 0.3)
    intent(path, "a", 0.1); intent(path, "b", 0.2)
    assert s.reserve(intent_id="a", now_ms=110, max_age_ms=20) == 0.1
    assert s.reserve(intent_id="b", now_ms=110, max_age_ms=20) == 0.2


def test_three_partial_fills_that_sum_to_the_filled_quantity_settle(tmp_path):
    # Terminal receipt: filled 0.3, delivered as fills of 0.1, 0.1 and 0.1.
    path, s = terminal_setup(tmp_path, status="filled", filled=0.3)
    with sqlite3.connect(path) as con:
        for fid in ("f1", "f2", "f3"):
            con.execute("INSERT INTO fills VALUES('a',0.1,?)", (fid,))
            con.execute("INSERT INTO reconcile_fill_deliveries VALUES('a','coinbase',?,1)", (fid,))
            con.execute("INSERT INTO live_position_fills VALUES('coinbase',?,'BTC/USD','sell',0.1)", (fid,))
    assert s.settle(intent_id="a")


def test_control_single_fill_of_the_same_total_settles(tmp_path):
    path, s = terminal_setup(tmp_path, status="filled", filled=0.3)
    with sqlite3.connect(path) as con:
        con.execute("INSERT INTO fills VALUES('a',0.3,'f1')")
        con.execute("INSERT INTO reconcile_fill_deliveries VALUES('a','coinbase','f1',1)")
        con.execute("INSERT INTO live_position_fills VALUES('coinbase','f1','BTC/USD','sell',0.3)")
    assert s.settle(intent_id="a")
