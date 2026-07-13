from __future__ import annotations

import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from services.execution.intent_lifecycle import (
    EXECUTION_STORE_STATUS_TRANSITIONS,
    execution_store_transition_allowed,
)
from storage.execution_store_sqlite import ExecutionStore


def _store(tmp_path) -> ExecutionStore:
    return ExecutionStore(path=str(tmp_path / "exec.sqlite"))


def _seed(store: ExecutionStore, intent_id: str, status: str) -> None:
    store.upsert_intent(
        {
            "intent_id": intent_id,
            "ts_ms": 1_700_000_000_000,
            "mode": "live",
            "exchange": "okx",
            "symbol": "BTC/USDT",
            "side": "buy",
            "order_type": "limit",
            "qty": 0.01,
            "limit_price": 100.0,
            "status": "pending",
            "reason": "test",
        }
    )
    if status != "pending":
        assert store.set_intent_status(intent_id=intent_id, status=status) is True


def _status(store: ExecutionStore, intent_id: str) -> str:
    con = sqlite3.connect(store.path)
    try:
        row = con.execute(
            "SELECT status FROM intents WHERE intent_id=?", (intent_id,)
        ).fetchone()
        return str(row[0]) if row else ""
    finally:
        con.close()


def test_legal_transition_applies_and_reports_true(tmp_path):
    s = _store(tmp_path)
    _seed(s, "i1", "pending")

    assert s.set_intent_status(intent_id="i1", status="submitted") is True
    assert _status(s, "i1") == "submitted"


def test_illegal_transition_is_refused_and_reports_false(tmp_path):
    s = _store(tmp_path)
    _seed(s, "i2", "pending")

    assert s.set_intent_status(intent_id="i2", status="filled") is False
    assert _status(s, "i2") == "pending"


def test_same_status_write_is_idempotent_and_reports_true(tmp_path):
    s = _store(tmp_path)
    _seed(s, "i3", "submitted")

    assert s.set_intent_status(intent_id="i3", status="submitted") is True
    assert _status(s, "i3") == "submitted"


def test_missing_intent_applies_nothing_and_reports_false(tmp_path):
    s = _store(tmp_path)

    assert s.set_intent_status(intent_id="nope", status="submitted") is False


@pytest.mark.parametrize(
    "terminal",
    sorted(st for st, succ in EXECUTION_STORE_STATUS_TRANSITIONS.items() if not succ),
)
def test_terminal_status_cannot_be_overwritten(tmp_path, terminal):
    s = _store(tmp_path)
    _seed(s, "t1", "submitted")
    assert s.set_intent_status(intent_id="t1", status=terminal) is True

    for attempt in ("submitted", "filled", "canceled", "error", "pending"):
        if attempt == terminal:
            continue
        assert s.set_intent_status(intent_id="t1", status=attempt) is False
        assert _status(s, "t1") == terminal


def test_concurrent_writers_exactly_one_transition_applies(tmp_path):
    s = _store(tmp_path)
    _seed(s, "race", "submitted")
    start = threading.Barrier(2)
    results: dict[str, bool] = {}

    def _writer(target: str) -> None:
        start.wait(timeout=5)
        results[target] = s.set_intent_status(
            intent_id="race", status=target, reason=target
        )

    with ThreadPoolExecutor(max_workers=2) as ex:
        f1 = ex.submit(_writer, "filled")
        f2 = ex.submit(_writer, "canceled")
        f1.result(timeout=30)
        f2.result(timeout=30)

    winners = [target for target, applied in results.items() if applied]
    assert len(winners) == 1
    assert _status(s, "race") == winners[0]


def test_concurrent_writers_cannot_resurrect_a_terminal_intent(tmp_path):
    s = _store(tmp_path)
    _seed(s, "term", "submitted")
    assert s.set_intent_status(intent_id="term", status="filled") is True
    start = threading.Barrier(8)
    outcomes: list[bool] = []
    lock = threading.Lock()

    def _writer(target: str) -> None:
        start.wait(timeout=5)
        applied = s.set_intent_status(intent_id="term", status=target)
        with lock:
            outcomes.append(applied)

    targets = ["submitted", "canceled", "error", "pending"] * 2
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = [ex.submit(_writer, target) for target in targets]
        for future in futures:
            future.result(timeout=30)

    assert not any(outcomes)
    assert _status(s, "term") == "filled"


@pytest.mark.parametrize(
    "current,target",
    [
        (current, target)
        for current in sorted(set(EXECUTION_STORE_STATUS_TRANSITIONS) | {"some_unknown"})
        for target in sorted(set(EXECUTION_STORE_STATUS_TRANSITIONS) | {"some_unknown"})
    ],
    ids=lambda value: str(value),
)
def test_store_behavior_matches_the_state_machine_for_every_pair(tmp_path, current, target):
    s = _store(tmp_path)
    intent_id = f"{current}__{target}"
    s.upsert_intent(
        {
            "intent_id": intent_id,
            "ts_ms": 1_700_000_000_000,
            "mode": "live",
            "exchange": "okx",
            "symbol": "BTC/USDT",
            "side": "buy",
            "order_type": "limit",
            "qty": 0.01,
            "limit_price": 100.0,
            "status": current,
            "reason": "seed",
        }
    )

    expected = execution_store_transition_allowed(current, target)
    applied = s.set_intent_status(intent_id=intent_id, status=target, reason="attempt")

    assert applied is expected
    assert _status(s, intent_id) == (target if expected else current)


def test_losing_writer_does_not_overwrite_the_reason(tmp_path):
    s = _store(tmp_path)
    _seed(s, "r1", "submitted")
    assert s.set_intent_status(intent_id="r1", status="filled", reason="winner") is True

    assert s.set_intent_status(intent_id="r1", status="submitted", reason="loser") is False

    con = sqlite3.connect(s.path)
    try:
        row = con.execute(
            "SELECT status, reason FROM intents WHERE intent_id=?", ("r1",)
        ).fetchone()
    finally:
        con.close()
    assert row[0] == "filled"
    assert row[1] == "winner"


def test_same_status_rewrite_updates_the_reason(tmp_path):
    s = _store(tmp_path)
    _seed(s, "p1", "pending")

    assert (
        s.set_intent_status(
            intent_id="p1", status="pending", reason="live_gate_block:x"
        )
        is True
    )

    con = sqlite3.connect(s.path)
    try:
        row = con.execute(
            "SELECT status, reason FROM intents WHERE intent_id=?", ("p1",)
        ).fetchone()
    finally:
        con.close()
    assert row[0] == "pending"
    assert row[1] == "live_gate_block:x"
