"""Selected actual submit method; real temporary dedupe DB, fake build/submit."""

import ast
from concurrent.futures import ThreadPoolExecutor
import inspect
import logging
from pathlib import Path
import socket
import threading
from types import SimpleNamespace

import pytest

from storage.order_dedupe_store_sqlite import OrderDedupeStore


ROOT = Path(__file__).resolve().parents[1]
APPLICATION = ROOT / "services/execution/exchange_client.py"
ORIGINAL = ROOT / "docs/review_artifacts/exchange_claim_owner_20261028/exchange_client_original.py"


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("network forbidden")
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)


def harness(tmp_path, *, source=APPLICATION, response=None, failure=None, store_factory=OrderDedupeStore,
            reconcile="inconclusive", submit=None):
    path = str(tmp_path / "fixture.sqlite")
    trace = []
    class SafeRetry(RuntimeError):
        pass
    ex = SimpleNamespace(close=lambda: trace.append("close"))
    def build():
        trace.append("build")
        if failure == "build":
            raise ValueError("invented build failure")
        return ex
    def place_order(*args, **kwargs):
        trace.append("place_order")
        if submit is not None:
            return submit()
        if failure == "submit":
            raise RuntimeError("invented definitive failure")
        return response if response is not None else {"id": "remote-1"}
    def recon(**kwargs):
        trace.append(("reconcile", kwargs["remote_order_id"]))
        return SimpleNamespace(outcome=reconcile)
    ns = {"inspect": inspect, "Path": Path, "_LOG": logging.getLogger("offline-claim-owner"),
          "ensure_dirs": lambda: None, "OrderDedupeStore": store_factory,
          "make_client_order_id": lambda *a: "client-1", "client_id_param": lambda *a: {"clientOrderId": "client-1"},
          "ExecutionContext": lambda **kwargs: kwargs, "place_order": place_order,
          "reconcile_ambiguous_submission": recon, "SafeToRetryAfterReconciliation": SafeRetry}
    tree = ast.parse(source.read_bytes())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ExchangeClient")
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "submit_order")
    helpers = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in {"_safe_close", "_is_ambiguous_submit_error"}]
    future = ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)
    module = ast.Module(body=[future, *helpers, method], type_ignores=[]); ast.fix_missing_locations(module)
    exec(compile(module, str(source), "exec"), ns)
    client = SimpleNamespace(exchange_id="coinbase", build=build)
    def invoke():
        return ns["submit_order"](client, symbol="ETH/USD", side="sell", order_type="limit", amount=1,
                                  price=10, client_id="client-1", intent_id="exit-1", exec_db=path)
    return invoke, trace, OrderDedupeStore(exec_db=path), SafeRetry


def claim(store):
    return store.claim(exchange_id="coinbase", intent_id="exit-1", symbol="ETH/USD", client_order_id="client-1")


def test_existing_created_claim_is_not_owned_and_cannot_submit(tmp_path):
    invoke, trace, store, _ = harness(tmp_path)
    assert claim(store)["_inserted"] is True
    with pytest.raises(RuntimeError, match="idempotency blocks"):
        invoke()
    assert trace == []


def test_archived_original_ignores_existing_created_claim(tmp_path):
    invoke, trace, store, _ = harness(tmp_path, source=ORIGINAL)
    claim(store)
    assert invoke()["id"] == "remote-1"
    assert trace == ["build", "place_order", "close"]


def test_new_claim_submits_once_and_replay_needs_no_client(tmp_path):
    invoke, trace, store, _ = harness(tmp_path)
    assert invoke() == {"id": "remote-1"}
    assert trace == ["build", "place_order", "close"]
    trace.clear()
    assert invoke()["idempotent_replay"] is True
    assert trace == []


@pytest.mark.parametrize("status", ["unknown", "submitted", "acked", "terminal", "unrecognized"])
def test_unresolved_or_invalid_dedupe_state_does_not_build(tmp_path, status):
    invoke, trace, store, _ = harness(tmp_path)
    claim(store)
    import sqlite3
    with sqlite3.connect(store.exec_db) as con:
        con.execute("UPDATE order_dedupe SET status=?", (status,))
    with pytest.raises(RuntimeError, match="idempotency blocks"):
        invoke()
    assert trace == []


def test_existing_error_retry_behavior_is_preserved_not_certified(tmp_path):
    invoke, trace, store, _ = harness(tmp_path)
    claim(store); store.mark_error(exchange_id="coinbase", intent_id="exit-1", error="known failure")
    assert invoke()["id"] == "remote-1" and trace == ["build", "place_order", "close"]


@pytest.mark.parametrize("failure", ["build", "submit"])
def test_pre_acknowledgement_definitive_failures_preserve_existing_error_lane(tmp_path, failure):
    invoke, trace, store, _ = harness(tmp_path, failure=failure)
    with pytest.raises((ValueError, RuntimeError)):
        invoke()
    assert store.get_by_intent("coinbase", "exit-1")["status"] == "error"
    assert trace == (["build"] if failure == "build" else ["build", "place_order", "close"])


@pytest.mark.parametrize("reconcile", ["inconclusive", "confirmed_not_placed", "confirmed_placed"])
def test_acknowledged_order_write_failure_cannot_reenter_error_retry_lane(tmp_path, reconcile):
    class FailingStore(OrderDedupeStore):
        def mark_submitted(self, **kwargs):
            raise RuntimeError("invented acknowledgement persistence failure")
    invoke, trace, store, safe_retry = harness(tmp_path, store_factory=FailingStore, reconcile=reconcile)
    with pytest.raises(RuntimeError) as raised:
        invoke()
    assert not isinstance(raised.value, safe_retry)
    assert store.get_by_intent("coinbase", "exit-1")["status"] == "unknown"
    assert ("reconcile", "remote-1") in trace and trace[-1] == "close"
    assert store.get_by_intent("coinbase", "exit-1")["remote_order_id"] == "remote-1"
    before = list(trace)
    with pytest.raises(RuntimeError, match="idempotency blocks"):
        invoke()
    assert trace == before


@pytest.mark.parametrize("existing_error", [False, True])
def test_two_created_or_error_claim_callers_only_one_reaches_fake_submit(tmp_path, existing_error):
    entered, release = threading.Event(), threading.Event()
    def submit():
        entered.set()
        assert release.wait(timeout=4)
        return {"id": "remote-1"}
    invoke, trace, store, _ = harness(tmp_path, submit=submit)
    if existing_error:
        claim(store)
        store.mark_error(exchange_id="coinbase", intent_id="exit-1", error="prior rejection")
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(invoke)
        try:
            assert entered.wait(timeout=2)
            second = pool.submit(invoke)
            with pytest.raises(RuntimeError, match="idempotency blocks"):
                second.result(timeout=2)
        finally:
            release.set()
        assert first.result(timeout=2)["id"] == "remote-1"
    assert trace == ["build", "place_order", "close"]


@pytest.mark.parametrize("outcome", ["inconclusive", "confirmed_not_placed", "confirmed_placed"])
def test_pre_acknowledgement_ambiguity_keeps_existing_reconciliation_contract(tmp_path, outcome):
    timeout_type = type("RequestTimeout", (Exception,), {})
    def submit():
        raise timeout_type("invented timeout")
    invoke, trace, store, safe_retry = harness(tmp_path, submit=submit, reconcile=outcome)
    with pytest.raises(RuntimeError) as raised:
        invoke()
    assert isinstance(raised.value, safe_retry) is (outcome == "confirmed_not_placed")
    assert store.get_by_intent("coinbase", "exit-1")["status"] == "unknown"
    assert ("reconcile", None) in trace and trace[-1] == "close"


@pytest.mark.parametrize("existing_error", [False, True])
def test_failed_unknown_write_retains_created_guard_against_second_submit(tmp_path, existing_error):
    class FailingStore(OrderDedupeStore):
        def mark_submitted(self, **kwargs):
            raise RuntimeError("invented acknowledgement write failure")
        def mark_unknown(self, **kwargs):
            raise RuntimeError("invented unknown-state write failure")
    invoke, trace, store, _ = harness(tmp_path, store_factory=FailingStore)
    if existing_error:
        claim(store)
        store.mark_error(exchange_id="coinbase", intent_id="exit-1", error="prior definitive rejection")
    with pytest.raises(RuntimeError):
        invoke()
    before = list(trace)
    with pytest.raises(RuntimeError) as second:
        invoke()
    assert trace == before and trace.count("place_order") == 1
    assert "idempotency blocks" in str(second.value)
    assert store.get_by_intent("coinbase", "exit-1")["status"] == "created"


def test_missing_claim_ownership_flag_cannot_authorize_a_build(tmp_path):
    class UnprovenStore(OrderDedupeStore):
        def claim(self, **kwargs):
            result = super().claim(**kwargs)
            result.pop("_submit_claimed")
            return result
    invoke, trace, _, _ = harness(tmp_path, store_factory=UnprovenStore)
    with pytest.raises(RuntimeError, match="idempotency blocks"):
        invoke()
    assert trace == []


def test_malformed_acknowledgement_is_not_a_definitive_error_retry(tmp_path):
    invoke, trace, store, safe_retry = harness(tmp_path, response=[], reconcile="confirmed_not_placed")
    with pytest.raises(RuntimeError) as raised:
        invoke()
    assert not isinstance(raised.value, safe_retry)
    assert store.get_by_intent("coinbase", "exit-1")["status"] == "unknown"
    assert trace[-1] == "close"


@pytest.mark.parametrize("status", ["error", "created"])
def test_known_remote_id_without_replay_state_cannot_resubmit(tmp_path, status):
    invoke, trace, store, _ = harness(tmp_path)
    claim(store)
    import sqlite3
    with sqlite3.connect(store.exec_db) as con:
        con.execute("UPDATE order_dedupe SET status=?,remote_order_id='known-remote'", (status,))
    with pytest.raises(RuntimeError, match="idempotency blocks"):
        invoke()
    assert trace == []


@pytest.mark.parametrize("field", ["exchange_id", "intent_id", "symbol", "client_order_id"])
def test_mismatched_claim_identity_never_builds_client(tmp_path, field):
    class MismatchedStore(OrderDedupeStore):
        def claim(self, **kwargs):
            result = super().claim(**kwargs)
            result[field] = "other"
            return result
    invoke, trace, _, _ = harness(tmp_path, store_factory=MismatchedStore)
    with pytest.raises(RuntimeError, match="claim_identity_mismatch"):
        invoke()
    assert trace == []


def test_rejected_v1_repeats_error_row_after_both_recovery_writes_fail(tmp_path):
    class FailingStore(OrderDedupeStore):
        def mark_submitted(self, **kwargs):
            raise RuntimeError("injected acknowledgement write failure")
        def mark_unknown(self, **kwargs):
            raise RuntimeError("injected unknown write failure")
    source = ROOT / "docs/review_artifacts/exchange_claim_owner_20261028/rejected_v1/exchange_client.py"
    invoke, trace, store, _ = harness(tmp_path, source=source, store_factory=FailingStore)
    claim(store); store.mark_error(exchange_id="coinbase", intent_id="exit-1", error="prior rejection")
    for _ in range(2):
        with pytest.raises(RuntimeError):
            invoke()
    assert trace.count("place_order") == 2
    assert store.get_by_intent("coinbase", "exit-1")["status"] == "error"


@pytest.mark.parametrize("status", ["created", "error", "unknown", "submitted", "acked", "terminal"])
def test_store_reclaims_only_matching_error_without_remote_id(tmp_path, status):
    import sqlite3
    store = OrderDedupeStore(exec_db=str(tmp_path / "fixture.sqlite"))
    claim(store)
    with sqlite3.connect(store.exec_db) as con:
        con.execute("UPDATE order_dedupe SET status=?", (status,))
    result = store.claim(exchange_id="coinbase", intent_id="exit-1", symbol="ETH/USD",
                         client_order_id="client-1", claim_error_for_submit=True)
    assert result["_inserted"] is False
    assert result["_submit_claimed"] is (status == "error")
    assert result["status"] == ("created" if status == "error" else status)


def test_default_store_claim_does_not_change_existing_error_policy(tmp_path):
    store = OrderDedupeStore(exec_db=str(tmp_path / "fixture.sqlite"))
    claim(store); store.mark_error(exchange_id="coinbase", intent_id="exit-1", error="prior rejection")
    result = claim(store)
    assert result["status"] == "error" and result["_submit_claimed"] is False
