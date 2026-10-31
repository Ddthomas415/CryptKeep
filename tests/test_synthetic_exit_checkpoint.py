"""Real SQLite fixture tests; no production database, schema initializer or SDK."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import replace
import json
import socket
import sqlite3
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from scripts.research import synthetic_exit_checkpoint as store
from services.execution.exit_deferral import ExitPolicy


BUCKET = ["coinbase", "invented-account", "exit-1"]
POLICY = ExitPolicy(100, 10, 40, 4)
INTENT = {"intent_id": "exit-1", "venue": "coinbase", "product_id": "ETH-USD", "side": "sell",
          "order_type": "market", "quantity": "2", "limit_price": None, "opaque": {"unchanged": True}}


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("network forbidden")
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)


def observation(**changes):
    product = {"id": "ETH-USD", "status": "online", "trading_disabled": False,
               "cancel_only": False, "limit_only": False, "post_only": False, "auction_mode": False}
    product.update(changes)
    return {"venue": "coinbase", "received_at_ms": 1000, "product": product}


def connect(path):
    return sqlite3.connect(path, timeout=3, isolation_level=None)


def seed(con, *, bucket=BUCKET, state=None):
    con.execute("INSERT INTO live_consumer_state(k,v) VALUES(?,?)",
                (store.key_for(bucket), store.encoded(state or store.initial_fixture_state(bucket, INTENT, POLICY))))


def raw(con, bucket=BUCKET):
    return con.execute("SELECT v FROM live_consumer_state WHERE k=?", (store.key_for(bucket),)).fetchone()[0]


def run(con, *, bucket=BUCKET, obs=None, now=1000, policy=POLICY, size=20000):
    return store.checkpoint(con, bucket=bucket, observation=obs if obs is not None else observation(),
                            now_ms=now, policy=policy, max_state_bytes=size)


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "fixture.sqlite"
    con = connect(path)
    con.execute("CREATE TABLE live_consumer_state(k TEXT PRIMARY KEY,v TEXT NOT NULL)")
    seed(con)
    yield path, con
    con.close()


def test_reservation_survives_restart_without_automatic_resubmit(database):
    path, con = database
    first = run(con)
    assert first["status"] == "RESERVED_OFFLINE_ONLY" and first["request"] is None
    assert not first["execution_authority"] and not first["evidence_authenticated"]
    assert first["checkpoint_progress"]["attempts"] == 1
    assert first["checkpoint_progress"]["outcome"] == "unknown"
    assert first["intent"] == INTENT
    con.close()
    with connect(path) as reopened:
        second = run(reopened, now=1001)
        assert second["status"] == "RECONCILE"
        assert second["reservation"] == first["reservation"]
        assert second["checkpoint_progress"]["attempts"] == 1


def test_two_real_sqlite_writers_cannot_both_reserve(database):
    path, _ = database
    barrier = threading.Barrier(2)
    def writer():
        con = connect(path)
        try:
            barrier.wait(timeout=3)
            return run(con)["status"]
        finally:
            con.close()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(writer) for _ in range(2)]
        results = [future.result(timeout=6) for future in futures]
    assert sorted(results) == ["RECONCILE", "RESERVED_OFFLINE_ONLY"]


def test_deferrals_and_alert_records_do_not_count_as_attempts(database):
    _, con = database
    for now in (1000, 1001, 1002):
        result = run(con, now=now, obs=observation(cancel_only=True))
        assert result["status"] == "DEFER" and result["reservation"] is None
        assert result["checkpoint_progress"]["attempts"] == 0
        assert result["recorded_alert_count"] == 1
    state = json.loads(raw(con))
    event = next(iter(state["alerts"].values()))
    assert event["first_recorded_ms"] == 1000 and not event["event"]["delivery_verified"]


@pytest.mark.parametrize("corruption", ["missing", "malformed", "duplicate", "schema", "counter", "scope", "alerts"])
def test_missing_or_corrupt_state_never_resets_or_reserves(database, corruption):
    _, con = database
    state = json.loads(raw(con))
    if corruption == "missing":
        con.execute("DELETE FROM live_consumer_state")
        before = None
    else:
        if corruption == "malformed":
            payload = "{unreadable"
        elif corruption == "duplicate":
            payload = raw(con)[:-1] + ',"schema":1}'
        else:
            if corruption == "schema": state["schema"] = 2
            if corruption == "counter": state["progress"]["attempts"] = True
            if corruption == "scope": state["bucket"][1] = "other-account"
            if corruption == "alerts": state["alerts"] = {"bad": None}
            payload = store.encoded(state)
        con.execute("UPDATE live_consumer_state SET v=?", (payload,))
        before = raw(con)
    result = run(con)
    assert result["status"] == "INCOMPLETE" and "reservation" not in result
    if before is None:
        assert con.execute("SELECT count(*) FROM live_consumer_state").fetchone()[0] == 0
    else:
        assert raw(con) == before


def test_account_buckets_are_isolated(database):
    _, con = database
    other = ["coinbase", "other-account", "exit-1"]
    seed(con, bucket=other)
    assert run(con)["status"] == run(con, bucket=other)["status"] == "RESERVED_OFFLINE_ONLY"
    assert json.loads(raw(con))["reservation"]["token"] != json.loads(raw(con, other))["reservation"]["token"]


@pytest.mark.parametrize("change", ["clock", "policy", "size", "transaction"])
def test_failures_preserve_prior_state_and_caller_transaction(database, change):
    _, con = database
    run(con)
    before = raw(con)
    kwargs = {}
    if change == "clock": kwargs["now"] = 999
    if change == "policy": kwargs["policy"] = replace(POLICY, max_attempts=5)
    if change == "size": kwargs["size"] = 1
    if change == "transaction": con.execute("BEGIN IMMEDIATE")
    assert run(con, **kwargs)["status"] == "INCOMPLETE"
    assert raw(con) == before
    if change == "transaction":
        assert con.in_transaction
        con.execute("ROLLBACK")


class FailingConnection:
    def __init__(self, connection, *, after_commit=False):
        self.connection, self.after_commit = connection, after_commit
    @property
    def in_transaction(self):
        return self.connection.in_transaction
    def execute(self, sql, *args):
        if sql == "COMMIT" and not self.after_commit:
            raise sqlite3.OperationalError("injected failure")
        result = self.connection.execute(sql, *args)
        if sql == "COMMIT" and self.after_commit:
            raise sqlite3.OperationalError("uncertain commit acknowledgement")
        return result


@pytest.mark.parametrize("after_commit", [False, True])
def test_write_failure_never_grants_reservation_and_uncertain_commit_is_retained(database, after_commit):
    _, con = database
    before = raw(con)
    result = run(FailingConnection(con, after_commit=after_commit))
    assert result["status"] == "INCOMPLETE" and "reservation" not in result
    assert not con.in_transaction
    if after_commit:
        assert run(con)["status"] == "RECONCILE"
    else:
        assert raw(con) == before


def test_absent_table_is_not_created(tmp_path):
    con = connect(tmp_path / "empty.sqlite")
    try:
        assert run(con)["status"] == "INCOMPLETE"
        assert con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() == []
    finally:
        con.close()


def test_explicit_cancelled_partial_fixture_retains_original_and_remaining_units(database):
    _, con = database
    state = json.loads(raw(con))
    state.update(revision=1, last_ms=980)
    state["progress"].update(attempts=1, last_attempt_ms=980, outcome="cancelled", confirmed_filled_quantity="0.5")
    con.execute("UPDATE live_consumer_state SET v=?", (store.encoded(state),))
    result = run(con)
    assert result["status"] == "RESERVED_OFFLINE_ONLY" and result["remaining_units"] == [3, 2]
    assert result["intent"] == INTENT and result["checkpoint_progress"]["attempts"] == 2


def test_attempt_ceiling_preserves_exit_and_records_operator_event(database):
    _, con = database
    state = json.loads(raw(con))
    state.update(revision=4, last_ms=980)
    state["progress"].update(attempts=4, last_attempt_ms=980, outcome="rejected")
    con.execute("UPDATE live_consumer_state SET v=?", (store.encoded(state),))
    result = run(con)
    assert result["status"] == "NEEDS_OPERATOR" and result["reservation"] is None
    assert result["intent"] == INTENT and result["checkpoint_progress"]["attempts"] == 4
    assert result["recorded_alert_count"] == 1


def test_updated_state_budget_and_corrupt_reservation_withhold_without_reset(database):
    _, con = database
    before = raw(con)
    assert run(con, size=len(before.encode()))["status"] == "INCOMPLETE"
    assert raw(con) == before
    run(con)
    state = json.loads(raw(con)); state["reservation"]["token"] = "tampered"
    con.execute("UPDATE live_consumer_state SET v=?", (store.encoded(state),))
    before = raw(con)
    assert run(con)["status"] == "INCOMPLETE" and raw(con) == before


@pytest.mark.parametrize("after_commit", [False, True])
def test_process_death_at_commit_boundary(database, after_commit):
    path, con = database
    before = raw(con)
    root = str(Path(__file__).resolve().parents[1])
    program = f"""
import os, socket, sqlite3, sys
sys.path.insert(0, {root!r})
def refuse(*args, **kwargs):
    raise AssertionError('network forbidden in disposable child')
socket.create_connection = socket.getaddrinfo = refuse
socket.socket.connect = refuse
from scripts.research.synthetic_exit_checkpoint import checkpoint
from services.execution.exit_deferral import ExitPolicy
con = sqlite3.connect({str(path)!r}, isolation_level=None)
class CrashConnection:
    @property
    def in_transaction(self):
        return con.in_transaction
    def execute(self, sql, *args):
        if sql == 'COMMIT' and not {after_commit!r}:
            os._exit(73)
        value = con.execute(sql, *args)
        if sql == 'COMMIT':
            os._exit(73)
        return value
checkpoint(CrashConnection(), bucket={BUCKET!r}, observation={observation()!r},
           now_ms=1000, policy=ExitPolicy(100,10,40,4), max_state_bytes=20000)
"""
    child = subprocess.run([sys.executable, "-I", "-B", "-c", program], timeout=5,
                           env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"},
                           capture_output=True, text=True)
    assert child.returncode == 73, child.stderr
    if after_commit:
        assert run(con)["status"] == "RECONCILE"
        assert json.loads(raw(con))["progress"]["attempts"] == 1
    else:
        assert raw(con) == before
        assert run(con)["status"] == "RESERVED_OFFLINE_ONLY"
