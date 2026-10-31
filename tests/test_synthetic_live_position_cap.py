"""Invented accounts only, real disposable SQLite transactions, no services."""

import asyncio
from fractions import Fraction
import json
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import threading

import pytest

from scripts.research import synthetic_live_position_cap as cap


BUCKET = ["invented-venue", "account-A", "asset-BTC"]


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("network forbidden in synthetic cap tests")
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket.socket, "connect_ex", refuse)


def snapshot(held="35", generation=1, orders=None, included=None):
    return {"bucket": list(BUCKET), "generation": generation,
            "identity_complete": True, "holdings_complete": True,
            "orders_complete": True, "fx_complete": True,
            "held_units": held, "mark_usd": "1",
            "holdings_ms": 100, "orders_ms": 100, "mark_ms": 100,
            "fx_ms": 100, "received_ms": 101,
            "orders": orders or [], "included_fills": included or {}}


def proposal(identity="one", units="10", quote="USD", side="buy"):
    return {"id": identity, "side": side, "base_asset_id": BUCKET[2],
            "quote_asset_id": quote, "units": units, "unit_usd_bound": "1",
            "bounded_spot_order": True, "spot_order": True}


def order(identity="one", filled="0", remaining="10", status="submitted"):
    return {"id": identity, "original_units": "10", "filled_units": filled,
            "remaining_units": remaining, "unit_usd_bound": "1", "status": status}


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "fixture.sqlite"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE live_consumer_state(k TEXT PRIMARY KEY,v TEXT)")
        connection.execute("INSERT INTO live_consumer_state VALUES(?,?)",
                           (cap.bucket_key(BUCKET), json.dumps(cap.initial_fixture_state())))
    return path


def run(path, *, snap=None, prop=None, bucket=None, **changes):
    options = dict(bucket=bucket or BUCKET, proposal=prop or proposal(),
                   snapshot=snap if snap is not None else snapshot(), now_ms=102,
                   max_age_ms=10, max_skew_ms=2, cap_usd="50")
    options.update(changes)
    with sqlite3.connect(path, timeout=2, isolation_level=None) as connection:
        return cap.admit(connection, **options)


def stored(path):
    with sqlite3.connect(path) as connection:
        return connection.execute("SELECT v FROM live_consumer_state ORDER BY k").fetchall()


@pytest.mark.parametrize("held,units,allowed,projected", [
    ("40", "25", False, 65), ("40", "10", True, 50),
    ("70", "1", False, 71), ("0", "50", True, 50)])
def test_cap_arithmetic(database, held, units, allowed, projected):
    result = run(database, snap=snapshot(held), prop=proposal(units=units))
    assert result["cap_allows"] is allowed
    assert Fraction(*result["projected_usd"]) == projected
    assert result["execution_authority"] is False and result["other_gates_required"] is True


def test_external_pending_buy_and_cross_pair(database):
    pending = order("manual", filled="2", remaining="8")
    result = run(database, snap=snapshot("40", orders=[pending], included={"manual": "2"}),
                 prop=proposal(units="5", quote="USDC"))
    assert result["reason"] == "position_cap" and Fraction(*result["projected_usd"]) == 53


def test_local_pending_survives_restart_and_other_pair(database):
    assert run(database)["cap_allows"]
    before = stored(database)
    result = run(database, prop=proposal("two", quote="USDC"))
    assert result["reason"] == "position_cap"
    assert stored(database) == before


def test_partial_fill_is_not_double_counted(database):
    assert run(database)["cap_allows"]
    snap = snapshot("41", 2, [order(filled="6", remaining="4")], {"one": "6"})
    result = run(database, snap=snap, prop=proposal("two", "5"))
    assert result["cap_allows"] and Fraction(*result["projected_usd"]) == 50


@pytest.mark.parametrize("kind", ["stale", "incoherent", "regressed", "unknown_cancel"])
def test_no_capacity_release_from_uncertain_fill_or_cancel(database, kind):
    assert run(database)["cap_allows"]
    before = stored(database)
    snap = snapshot("35", 2, [order(filled="6", remaining="4")], {"one": "6"})
    if kind == "stale": snap["holdings_ms"] = 0
    if kind == "incoherent": snap["included_fills"] = {}
    if kind == "regressed": snap["generation"] = 0
    if kind == "unknown_cancel": snap["orders"] = []; snap["included_fills"] = {}
    result = run(database, snap=snap, prop=proposal("two", "10"))
    assert not result["cap_allows"]
    if kind != "unknown_cancel":
        assert stored(database) == before
    else:
        state = json.loads(stored(database)[0][0])
        assert set(state["reservations"]) == {"one"}
        assert state["reservations"]["one"]["remaining"] == [10, 1]


def test_cancel_final_fill_baseline_and_tombstone(database):
    assert run(database)["cap_allows"]
    snap = snapshot("41", 2, [order(filled="6", remaining="0", status="cancelled")], {"one": "6"})
    assert run(database, snap=snap, prop=proposal("two", "9"))["cap_allows"]
    assert run(database, snap=snap)["reason"] == "already_known_intent"


@pytest.mark.parametrize("status", ["queued", "submitting", "submitted", "held", "unknown"])
def test_all_open_statuses_reserve(database, status):
    snap = snapshot(orders=[order("external", status=status)])
    assert run(database, snap=snap)["reason"] == "position_cap"


@pytest.mark.parametrize("field,value", [
    ("identity_complete", False), ("holdings_complete", False),
    ("orders_complete", False), ("fx_complete", False), ("held_units", None),
    ("held_units", "-1"), ("held_units", "NaN"), ("mark_usd", "0"),
    ("mark_usd", "Infinity"), ("mark_ms", 103), ("orders_ms", 97),
    ("received_ms", 103), ("generation", True)])
def test_incomplete_or_invalid_evidence_refuses_without_mutation(database, field, value):
    before = stored(database); snap = snapshot(); snap[field] = value
    assert not run(database, snap=snap)["cap_allows"]
    assert stored(database) == before


def test_reducing_sell_ignores_missing_increase_data_but_not_oversell(database):
    reduction = {"bucket": BUCKET, "identity_complete": True, "pending_sells_complete": True,
                 "held_units": "65", "pending_sell_units": "0", "as_of_ms": 100, "received_ms": 101}
    prop = proposal(units="20", side="sell")
    result = run(database, snap={}, prop=prop, cap_usd=None, reduction=reduction)
    assert result["cap_allows"] and result["reason"] == "reducing_cap_only"
    reduction["pending_sell_units"] = "50"
    assert run(database, snap={}, prop=prop, reduction=reduction)["reason"] == "not_verified_reducing"
    assert not run(database, snap={}, prop=prop)["cap_allows"]


def test_account_identity_isolation(database):
    bucket = [BUCKET[0], "account-B", BUCKET[2]]
    with sqlite3.connect(database) as connection:
        connection.execute("INSERT INTO live_consumer_state VALUES(?,?)",
                           (cap.bucket_key(bucket), json.dumps(cap.initial_fixture_state())))
    assert run(database)["cap_allows"]
    snap = snapshot(); snap["bucket"] = bucket
    assert run(database, snap=snap, bucket=bucket)["cap_allows"]
    assert not run(database, bucket=bucket)["cap_allows"]


@pytest.mark.parametrize("corrupt", ["missing", "unreadable", "negative", "duplicate"])
def test_corrupt_or_missing_state_never_resets(database, corrupt):
    with sqlite3.connect(database) as connection:
        if corrupt == "missing": connection.execute("DELETE FROM live_consumer_state")
        else:
            value = "bad json"
            if corrupt == "negative":
                value = json.dumps(dict(cap.initial_fixture_state(), reservations={"bad": {"original": [-1, 1]}}))
            if corrupt == "duplicate": value = '{"schema":1,"schema":1}'
            connection.execute("UPDATE live_consumer_state SET v=?", (value,))
    before = stored(database)
    assert not run(database)["cap_allows"] and stored(database) == before


def test_real_mixed_sync_async_concurrent_admission(database):
    barrier = threading.Barrier(2); outcomes = []
    def sync_worker():
        barrier.wait(timeout=3); outcomes.append(run(database, prop=proposal("sync")))
    thread = threading.Thread(target=sync_worker)
    thread.start()
    def factory():
        barrier.wait(timeout=3)
        return sqlite3.connect(database, timeout=2, isolation_level=None)
    async_result = asyncio.run(cap.admit_async(factory, bucket=BUCKET, proposal=proposal("async", quote="USDC"),
        snapshot=snapshot(), now_ms=102, max_age_ms=10, max_skew_ms=2, cap_usd="50"))
    thread.join(timeout=4)
    assert not thread.is_alive() and len(outcomes) == 1
    assert sum(r["cap_allows"] for r in outcomes + [async_result]) == 1
    assert {r["reason"] for r in outcomes + [async_result]} == {"reserved_cap_only", "position_cap"}


def test_crash_after_commit_retains_reservation(database):
    root = Path(__file__).resolve().parents[1]
    code = ("import sys,sqlite3,json,os;sys.path.insert(0,sys.argv[1]);"
            "from scripts.research.synthetic_live_position_cap import admit;"
            "c=sqlite3.connect(sys.argv[2],isolation_level=None);"
            "kwargs=json.loads(sys.argv[3]);r=admit(c,**kwargs);"
            "os._exit(0 if r['cap_allows'] else 2)")
    kwargs = dict(bucket=BUCKET, proposal=proposal(), snapshot=snapshot(), now_ms=102,
                  max_age_ms=10, max_skew_ms=2, cap_usd="50")
    result = subprocess.run([sys.executable, "-I", "-S", "-B", "-c", code, str(root),
        str(database), json.dumps(kwargs)], timeout=5, env={"PATH": "/usr/bin:/bin"}, capture_output=True)
    assert result.returncode == 0
    assert run(database, prop=proposal("later"))["reason"] == "position_cap"


def test_transaction_failure_rolls_back_reservation(database):
    class BrokenCommit:
        def __init__(self, connection): self.connection = connection
        @property
        def in_transaction(self): return self.connection.in_transaction
        def execute(self, sql, args=()):
            if sql == "COMMIT": raise sqlite3.OperationalError("invented failure")
            return self.connection.execute(sql, args)
    before = stored(database)
    with sqlite3.connect(database, isolation_level=None) as connection:
        result = cap.admit(BrokenCommit(connection), bucket=BUCKET, proposal=proposal(), snapshot=snapshot(),
            now_ms=102, max_age_ms=10, max_skew_ms=2, cap_usd="50")
    assert not result["cap_allows"] and stored(database) == before


def test_manual_obligation_persists_even_when_first_proposal_refused(database):
    snap = snapshot("40", orders=[order("manual")])
    assert run(database, snap=snap, prop=proposal(units="1"))["reason"] == "position_cap"
    snap = snapshot("40", 2)
    assert run(database, snap=snap, prop=proposal(units="1"))["reason"] == "position_cap"
    snap = snapshot("40", 3, [order("manual", remaining="0", status="cancelled")])
    assert run(database, snap=snap, prop=proposal(units="1"))["cap_allows"]


def test_explicit_freshness_and_usd_bounds(database):
    snap = snapshot(); snap["mark_usd"] = "2"
    assert run(database, snap=snap)["reason"] == "position_cap"
    prop = proposal(); prop["unit_usd_bound"] = "2"
    assert run(database, snap=snapshot(generation=2), prop=prop)["reason"] == "position_cap"
    prop = proposal(); prop["bounded_spot_order"] = False
    assert run(database, prop=prop)["reason"] == "bounded_spot_order_required"
    assert run(database, max_age_ms=1)["reason"] == "stale_future_or_skewed_evidence"
    assert run(database, snap=snapshot("49.999", 3), prop=proposal(units="0.001"))["cap_allows"]


def test_duplicate_ids_and_non_spot_refused(database):
    assert not run(database, snap=snapshot(orders=[order(), order()]))["cap_allows"]
    prop = proposal(); prop["spot_order"] = False
    assert run(database, prop=prop)["reason"] == "spot_order_required"


def test_async_cancellation_does_not_release_committed_reservation(database):
    started, release = threading.Event(), threading.Event()
    def factory():
        started.set()
        assert release.wait(timeout=3)
        return sqlite3.connect(database, timeout=2, isolation_level=None)
    async def exercise():
        task = asyncio.create_task(cap.admit_async(factory, bucket=BUCKET, proposal=proposal(),
            snapshot=snapshot(), now_ms=102, max_age_ms=10, max_skew_ms=2, cap_usd="50"))
        assert await asyncio.to_thread(started.wait, 2)
        task.cancel()
        try:
            with pytest.raises(asyncio.CancelledError):
                await task
        finally:
            release.set()
    asyncio.run(exercise())
    assert run(database, prop=proposal("later"))["reason"] == "position_cap"


def test_hard_exit_inside_transaction_rolls_back(database):
    root = Path(__file__).resolve().parents[1]
    code = """
import json, os, sqlite3, sys
sys.path.insert(0, sys.argv[1])
from scripts.research.synthetic_live_position_cap import admit
class Crash(sqlite3.Connection):
    def execute(self, sql, args=()):
        result = super().execute(sql, args)
        if sql.startswith('UPDATE live_consumer_state'):
            os._exit(17)
        return result
c = sqlite3.connect(sys.argv[2], isolation_level=None, factory=Crash)
admit(c, **json.loads(sys.argv[3]))
"""
    kwargs = dict(bucket=BUCKET, proposal=proposal(), snapshot=snapshot(), now_ms=102,
                  max_age_ms=10, max_skew_ms=2, cap_usd="50")
    before = stored(database)
    result = subprocess.run([sys.executable, "-I", "-S", "-B", "-c", code, str(root),
        str(database), json.dumps(kwargs)], timeout=5, env={"PATH": "/usr/bin:/bin"}, capture_output=True)
    assert result.returncode == 17 and stored(database) == before
    assert run(database)["cap_allows"]


@pytest.mark.parametrize("field", ["included_fills", "orders"])
def test_malformed_snapshot_collections_fail_closed(database, field):
    snap = snapshot(); snap[field] = None
    assert run(database, snap=snap)["reason"] == "incomplete_snapshot"


def test_clock_is_sampled_after_real_lock_wait(database):
    now = [102]; ready = threading.Event(); outputs = []
    blocker = sqlite3.connect(database, isolation_level=None)
    blocker.execute("BEGIN IMMEDIATE")
    def worker():
        ready.set()
        outputs.append(run(database, now_ms=lambda: now[0]))
    thread = threading.Thread(target=worker); thread.start()
    assert ready.wait(timeout=2)
    now[0] = 113
    blocker.execute("ROLLBACK"); blocker.close()
    thread.join(timeout=4)
    assert not thread.is_alive() and len(outputs) == 1
    assert outputs[0]["reason"] == "stale_future_or_skewed_evidence"


@pytest.mark.parametrize("terminal", [False, True])
@pytest.mark.parametrize("coverage", ["missing", "regressed"])
def test_retained_fill_baseline_required_when_order_disappears(database, terminal, coverage):
    assert run(database)["cap_allows"]
    filled = "10" if terminal else "6"
    snap = snapshot("45" if terminal else "41", 2,
        [order(filled=filled, remaining="0" if terminal else "4",
               status="filled" if terminal else "submitted")], {"one": filled})
    assert run(database, snap=snap, prop=proposal("denied", "20"))["reason"] == "position_cap"
    before = stored(database)
    included = {} if coverage == "missing" else {"one": str(int(filled) - 1)}
    result = run(database, snap=snapshot("35", 3, included=included), prop=proposal("later"))
    assert not result["cap_allows"]
    assert result["reason"] == "retained_fill_baseline_unresolved"
    assert stored(database) == before


@pytest.mark.parametrize("terminal", [False, True])
def test_legitimate_holding_reduction_keeps_known_fill_coverage(database, terminal):
    assert run(database)["cap_allows"]
    filled = "10" if terminal else "6"
    snap = snapshot("45" if terminal else "41", 2,
        [order(filled=filled, remaining="0" if terminal else "4",
               status="filled" if terminal else "submitted")], {"one": filled})
    assert not run(database, snap=snap, prop=proposal("denied", "20"))["cap_allows"]
    result = run(database, snap=snapshot("30", 3, included={"one": filled}), prop=proposal("later"))
    assert result["cap_allows"]
    assert Fraction(*result["projected_usd"]) == (40 if terminal else 44)
