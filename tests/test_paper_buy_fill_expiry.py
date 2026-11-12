from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import copy
import json
import sqlite3
import threading

import pytest

from services.execution.paper_buy_policy import (
    PAPER_BUY_CREATED_TS, PAPER_BUY_MAX_AGE_S, buy_age_verdict,
)
from storage import paper_trading_sqlite as store


CREATED = datetime(2026, 11, 3, tzinfo=timezone.utc)


@pytest.fixture
def db(monkeypatch, tmp_path):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "paper.sqlite")
    result = store.PaperTradingSQLite()
    result.set_state("cash_quote", "1000")
    result.set_state("realized_pnl", "0")
    return result


def insert(db, *, origin=CREATED.isoformat(), legacy=None, **changes):
    row = dict(order_id="order-1", client_order_id="buy-1", venue="coinbase",
               symbol="BTC/USD", side="buy", order_type="market", qty=1.0,
               ts="2099-01-01T00:00:00Z", status="new",
               meta={PAPER_BUY_CREATED_TS: origin})
    row.update(changes)
    db.insert_order(row)
    if legacy is not None:
        with sqlite3.connect(store.DB_PATH) as con:
            con.execute("UPDATE paper_orders SET created_ts=? WHERE order_id=?",
                        (legacy, row["order_id"]))
    return db.get_order_by_client_id(row["client_order_id"])


def fill(db, order, *, clock=lambda: CREATED + timedelta(seconds=30), **changes):
    args = dict(order=order, ts="2000-01-01T00:00:00Z", price=100.0,
                qty=1.0, fee=1.0, fee_currency="USD", clock=clock)
    args.update(changes)
    return db.apply_fill(**args)


def unchanged_accounting(db):
    assert db.list_fills() == []
    assert db.list_positions() == []
    assert float(db.get_state("cash_quote")) == 1000.0
    assert float(db.get_state("realized_pnl")) == 0.0


@pytest.mark.parametrize("age,ok", [(119.999, True), (120, False), (120.001, False)])
@pytest.mark.parametrize("representation", ["datetime", "iso", "z", "naive", "offset", "epoch"])
def test_policy_exact_boundary_and_timestamp_forms(age, ok, representation, monkeypatch):
    monkeypatch.setenv("CBP_MAX_INTENT_AGE_SEC", "999999")
    now = CREATED + timedelta(seconds=age)
    created = CREATED
    if representation == "iso":
        created, now = created.isoformat(), now.isoformat()
    elif representation == "z":
        created, now = created.isoformat().replace("+00:00", "Z"), now.isoformat().replace("+00:00", "Z")
    elif representation == "naive":
        created, now = created.replace(tzinfo=None), now.replace(tzinfo=None)
    elif representation == "offset":
        created = created.astimezone(timezone(timedelta(hours=-5))).isoformat()
    elif representation == "epoch":
        created, now = created.timestamp(), now.timestamp()
    verdict = buy_age_verdict(created, now)
    assert PAPER_BUY_MAX_AGE_S == 120
    assert verdict["ok"] is ok
    assert verdict["age_s"] == pytest.approx(age, abs=1e-6)
    assert verdict["reason"] == ("ok" if ok else "paper_buy_ttl:expired")


@pytest.mark.parametrize("value", [None, "", "broken", float("nan"), float("inf"),
                                  -1, 0, True, 10 ** 1000, [], {}])
def test_policy_invalid_creation_and_now_fail_closed(value):
    assert not buy_age_verdict(value, CREATED)["ok"]
    assert buy_age_verdict(CREATED, value)["reason"] == "paper_buy_ttl:invalid_now"


def test_policy_future_even_one_microsecond_fails_closed():
    assert buy_age_verdict(CREATED + timedelta(microseconds=1), CREATED)["reason"] == "paper_buy_ttl:future_created_ts"


@pytest.mark.parametrize("age,status", [(119.999, "filled"), (120, "expired")])
def test_fill_exact_boundary(db, age, status):
    order = insert(db)
    result = fill(db, order, clock=lambda: CREATED + timedelta(seconds=age))
    assert result["ok"] is (status == "filled")
    assert db.get_order_by_order_id(order["order_id"])["status"] == status
    if status == "expired":
        assert result["reason"] == "paper_buy_ttl:expired"
        assert db.get_order_by_order_id(order["order_id"])["reject_reason"] == result["reason"]
        unchanged_accounting(db)
    else:
        assert float(db.get_state("cash_quote")) == 899
        assert db.get_position("BTC/USD")["qty"] == 1


def test_default_clock_does_not_use_historical_fill_evidence_time(db):
    order = insert(db, origin="2000-01-01T00:00:00Z")
    result = db.apply_fill(order=order, ts="2000-01-01T00:00:01Z", price=100,
                           qty=1, fee=1, fee_currency="USD")
    assert result["reason"] == "paper_buy_ttl:expired"
    unchanged_accounting(db)


@pytest.mark.parametrize("origin,reason", [(None, "missing_created_ts"), ("bad", "invalid_created_ts"),
                                         ((CREATED + timedelta(seconds=1)).isoformat(), "future_created_ts")])
def test_bad_reserved_origin_never_falls_back_to_legacy(db, origin, reason):
    order = insert(db, origin=origin, legacy=CREATED.isoformat())
    result = fill(db, order, clock=lambda: CREATED)
    assert result["reason"] == "paper_buy_ttl:" + reason
    stored = db.get_order_by_order_id(order["order_id"])
    assert stored["status"] == "rejected" and stored["reject_reason"] == result["reason"]
    unchanged_accounting(db)


@pytest.mark.parametrize("legacy,reason", [("2000-01-01T00:00:00Z", "expired"),
                                         ("bad", "invalid_created_ts"),
                                         ((CREATED + timedelta(seconds=60)).isoformat(), "future_created_ts")])
def test_legacy_uses_stored_created_not_decision_ts(db, legacy, reason):
    order = insert(db, meta=None, legacy=legacy, ts=CREATED.isoformat())
    result = fill(db, order)
    assert result["reason"] == "paper_buy_ttl:" + reason
    assert db.get_order_by_order_id(order["order_id"])["status"] == ("expired" if reason == "expired" else "rejected")
    unchanged_accounting(db)


def test_legacy_fresh_created_allows_old_decision_timestamp(db):
    order = insert(db, meta={}, legacy=CREATED.isoformat(), ts="2000-01-01T00:00:00Z")
    assert fill(db, order)["ok"]


def test_stale_or_forged_caller_side_metadata_and_time_cannot_bypass(db):
    order = insert(db, origin="2000-01-01T00:00:00Z")
    caller = copy.deepcopy(order)
    caller.update(side="sell", created_ts=CREATED.isoformat(), ts=CREATED.isoformat(),
                  meta={PAPER_BUY_CREATED_TS: CREATED.isoformat()})
    assert fill(db, caller)["reason"] == "paper_buy_ttl:expired"
    unchanged_accounting(db)


def test_stored_origin_update_after_caller_read_is_authoritative(db):
    order = insert(db)
    with sqlite3.connect(store.DB_PATH) as con:
        con.execute("UPDATE paper_orders SET meta_json=? WHERE order_id=?",
                    (json.dumps({PAPER_BUY_CREATED_TS: "2000-01-01T00:00:00Z"}), order["order_id"]))
    assert fill(db, order)["reason"] == "paper_buy_ttl:expired"
    unchanged_accounting(db)


def test_malformed_stored_json_rejected_durably(db):
    order = insert(db)
    with sqlite3.connect(store.DB_PATH) as con:
        con.execute("UPDATE paper_orders SET meta_json='{' WHERE order_id=?", (order["order_id"],))
    result = fill(db, order)
    assert result["reason"] == "invalid_stored_order_meta"
    with sqlite3.connect(store.DB_PATH) as con:
        assert con.execute("SELECT status, reject_reason FROM paper_orders").fetchone() == ("rejected", result["reason"])
    unchanged_accounting(db)


@pytest.mark.parametrize("raw", [
    '{"paper_buy_created_ts":"2000-01-01T00:00:00Z","paper_buy_created_ts":"2026-11-03T00:00:00Z"}',
    '{"paper_buy_created_ts":"2026-11-03T00:00:00Z","nested":{"x":1,"x":2}}',
    '{"paper_buy_created_ts":NaN}', '{"paper_buy_created_ts":Infinity}',
    '{"paper_buy_created_ts":1e999}',
    '{"paper_buy_created_ts":"2026-11-03T00:00:00Z","nested":[NaN]}',
    '[]', '"not-an-object"',
])
@pytest.mark.parametrize("operation", ["fill", "expire"])
def test_strict_stored_metadata_rejects_ambiguous_or_nonfinite_payload(db, raw, operation):
    order = insert(db)
    with sqlite3.connect(store.DB_PATH) as con:
        con.execute("UPDATE paper_orders SET meta_json=? WHERE order_id=?", (raw, order["order_id"]))
    if operation == "fill":
        result = fill(db, order)
        assert not result["ok"]
    else:
        result = db.expire_buy_order("buy-1", clock=lambda: CREATED)
        assert result["state"] == "rejected"
    assert result["reason"] == "invalid_stored_order_meta"
    with sqlite3.connect(store.DB_PATH) as con:
        assert con.execute("SELECT status, reject_reason FROM paper_orders").fetchone() == ("rejected", result["reason"])
    unchanged_accounting(db)


@pytest.mark.parametrize("bad_clock", [lambda: "bad", lambda: None, lambda: 1 / 0])
def test_invalid_or_failing_clock_rejects_without_accounting(db, bad_clock):
    order = insert(db)
    assert fill(db, order, clock=bad_clock)["reason"] == "paper_buy_ttl:invalid_now"
    assert db.get_order_by_order_id(order["order_id"])["status"] == "rejected"
    unchanged_accounting(db)


def test_injected_clock_is_fresh_fill_and_position_evidence(db):
    order = insert(db)
    now = CREATED + timedelta(seconds=45)
    assert fill(db, order, clock=lambda: now.isoformat())["ok"]
    assert db.list_fills()[0]["ts"] == now.isoformat()
    assert db.get_position("BTC/USD")["updated_ts"] == now.isoformat()


def test_filled_idempotence_precedes_age_metadata_and_clock(db):
    order = insert(db)
    first = fill(db, order)
    with sqlite3.connect(store.DB_PATH) as con:
        con.execute("UPDATE paper_orders SET meta_json='{' WHERE order_id=?", (order["order_id"],))
    retry = fill(db, order, clock=lambda: 1 / 0)
    assert first["ok"] and retry["ok"] and retry["idempotent"]
    assert len(db.list_fills()) == 1
    assert float(db.get_state("cash_quote")) == 899
    assert db.get_position("BTC/USD")["qty"] == 1


@pytest.mark.parametrize("status", ["expired", "rejected", "canceled", "cancelled", "superseded"])
def test_terminal_buy_cannot_fill_even_with_fresh_clock(db, status):
    order = insert(db, status=status, reject_reason="prior_reason")
    assert not fill(db, order)["ok"]
    assert db.get_order_by_order_id(order["order_id"])["status"] == status
    unchanged_accounting(db)


def test_expire_missing_and_fresh_are_read_only(db):
    missing = db.expire_buy_order("missing", clock=lambda: CREATED)
    assert missing["state"] == "missing" and missing["order"] is None
    order = insert(db)
    fresh = db.expire_buy_order("buy-1", clock=lambda: CREATED + timedelta(seconds=119.999))
    assert fresh["state"] == "new" and fresh["order"] == order
    unchanged_accounting(db)


@pytest.mark.parametrize("stored_age,queue_age", [(120, 30), (30, 120), (120, None)])
def test_expire_uses_oldest_valid_origin(db, stored_age, queue_age):
    now = CREATED + timedelta(seconds=300)
    order = insert(db, origin=(now - timedelta(seconds=stored_age)).isoformat())
    supplied = None if queue_age is None else (now - timedelta(seconds=queue_age)).isoformat()
    result = db.expire_buy_order("buy-1", created_ts=supplied, clock=lambda: now)
    assert result["state"] == "expired" and result["reason"] == "paper_buy_ttl:expired"
    assert result["order"] == db.get_order_by_order_id(order["order_id"])
    assert result["order"]["reject_reason"] == result["reason"]
    unchanged_accounting(db)


@pytest.mark.parametrize("bad_origin", ["bad", "", (CREATED + timedelta(seconds=60)).isoformat()])
@pytest.mark.parametrize("source", ["stored", "queue", "legacy"])
def test_expire_invalid_either_source_rejects(db, bad_origin, source):
    changes = {"origin": bad_origin} if source == "stored" else {}
    if source == "legacy":
        changes.update(meta=None, legacy=bad_origin)
    order = insert(db, **changes)
    result = db.expire_buy_order("buy-1", created_ts=bad_origin if source == "queue" else None,
                                 clock=lambda: CREATED)
    assert result["state"] == "rejected"
    assert result["order"] == db.get_order_by_order_id(order["order_id"])
    unchanged_accounting(db)


@pytest.mark.parametrize("status", ["filled", "expired", "rejected", "canceled", "cancelled", "superseded"])
def test_expire_never_resurrects_or_reclassifies_terminal(db, status):
    order = insert(db, status=status, reject_reason="prior_reason")
    result = db.expire_buy_order("buy-1", created_ts="bad", clock=lambda: 1 / 0)
    assert result["state"] == status and result["order"] == order
    assert db.get_order_by_order_id(order["order_id"]) == order


@pytest.mark.parametrize("age", [120, 100000])
def test_sell_never_expires_or_calls_buy_clock(db, age):
    db.upsert_position("BTC/USD", 1.0, 100.0, 0.0)
    order = insert(db, side="sell", origin="bad", legacy="bad")
    result = db.expire_buy_order("buy-1", created_ts="bad", clock=lambda: 1 / 0)
    assert result["state"] == "new" and result["order"] == order
    result = fill(db, order, clock=lambda: 1 / 0, ts=(CREATED + timedelta(seconds=age)).isoformat())
    assert result["ok"]
    assert db.get_order_by_order_id(order["order_id"])["status"] == "filled"


@pytest.mark.parametrize("operation", ["fill", "expire"])
@pytest.mark.parametrize("injected", [True, False])
def test_clock_sampled_after_waiting_for_write_lock(db, monkeypatch, operation, injected):
    order = insert(db)
    connecting = threading.Event()
    clock_called = threading.Event()
    original_connect = store._connect
    con = original_connect()
    con.execute("BEGIN IMMEDIATE")
    current = [CREATED + timedelta(seconds=119)]

    def connect():
        result = original_connect()
        connecting.set()
        return result

    def clock():
        clock_called.set()
        return current[0]

    class ClockDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return clock()

    if not injected:
        monkeypatch.setattr(store, "datetime", ClockDateTime)
    monkeypatch.setattr(store, "_connect", connect)
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            kwargs = {"clock": clock if injected else None}
            future = (pool.submit(fill, db, order, **kwargs) if operation == "fill" else
                      pool.submit(db.expire_buy_order, "buy-1", **kwargs))
            assert connecting.wait(3)
            assert not clock_called.is_set()
            current[0] = CREATED + timedelta(seconds=120)
            con.execute("COMMIT")
            assert future.result(timeout=5)["reason"] == "paper_buy_ttl:expired"
    finally:
        con.close()
    unchanged_accounting(db)


@pytest.mark.parametrize("winner", ["expiry", "fill"])
def test_expiry_and_fill_serialize_without_overwriting_winner(db, winner):
    order = insert(db)
    inside_lock = threading.Event()
    release = threading.Event()

    def blocked_clock():
        inside_lock.set()
        assert release.wait(3)
        return CREATED + timedelta(seconds=120 if winner == "expiry" else 119)

    def expire(clock):
        return db.expire_buy_order("buy-1", clock=clock)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(expire, blocked_clock) if winner == "expiry" else pool.submit(fill, db, order, clock=blocked_clock)
        assert inside_lock.wait(3)
        second = pool.submit(fill, db, order) if winner == "expiry" else pool.submit(expire, lambda: CREATED + timedelta(seconds=120))
        release.set()
        one, two = first.result(timeout=5), second.result(timeout=5)
    if winner == "expiry":
        assert one["state"] == "expired" and not two["ok"]
        assert db.get_order_by_order_id(order["order_id"])["status"] == "expired"
        unchanged_accounting(db)
    else:
        assert one["ok"] and two["state"] == "filled"
        assert db.get_order_by_order_id(order["order_id"])["status"] == "filled"
        assert len(db.list_fills()) == 1
        assert float(db.get_state("cash_quote")) == 899


@pytest.mark.parametrize("operation", ["fill", "expire"])
def test_expiry_write_rolls_back_atomically_on_failure(db, monkeypatch, operation):
    order = insert(db)
    original = db._update_order_status_conn

    def fail_after_write(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError("simulated commit failure")

    monkeypatch.setattr(db, "_update_order_status_conn", fail_after_write)
    with pytest.raises(RuntimeError, match="simulated commit failure"):
        clock = lambda: CREATED + timedelta(seconds=120)
        if operation == "fill":
            fill(db, order, clock=clock)
        else:
            db.expire_buy_order("buy-1", clock=clock)
    assert db.get_order_by_order_id(order["order_id"]) == order
    unchanged_accounting(db)


def buy_terminal(db, client="buy-1"):
    raw = db.get_state("paper_buy_terminal:" + client)
    return json.loads(raw) if raw is not None else None


@pytest.mark.parametrize("created,reason,state", [
    (CREATED.isoformat(), "paper_buy_ttl:expired", "expired"),
    ("bad", "paper_buy_ttl:invalid_created_ts", "rejected"),
    (None, "paper_buy_ttl:missing_created_ts", "rejected"),
    (float("nan"), "paper_buy_ttl:invalid_created_ts", "rejected"),
    ((CREATED + timedelta(seconds=121)).isoformat(), "paper_buy_ttl:future_created_ts", "rejected"),
])
def test_missing_expiry_fence_blocks_late_fresh_order_after_restart(db, created, reason, state):
    receipt = db.expire_buy_order("buy-1", created_ts=created, fence_missing=True,
                                  clock=lambda: CREATED + timedelta(seconds=120))
    assert receipt == {"state": state, "reason": reason, "order": None}
    terminal = buy_terminal(db)
    assert terminal["state"] == state and terminal["reason"] == reason
    assert terminal["client_order_id"] == "buy-1"
    assert "created_ts" in terminal
    assert db.list_orders() == []
    restarted = store.PaperTradingSQLite()
    order = insert(restarted, origin=(CREATED + timedelta(seconds=120)).isoformat())
    forged = {**order, "side": "sell", "client_order_id": "another"}
    result = fill(restarted, forged, clock=lambda: CREATED + timedelta(seconds=121))
    assert not result["ok"] and result["reason"] == reason
    canonical = restarted.get_order_by_order_id(order["order_id"])
    assert canonical["status"] == state and canonical["reject_reason"] == reason
    assert buy_terminal(restarted) == terminal
    unchanged_accounting(restarted)


@pytest.mark.parametrize("fence_missing,age", [(False, 120), (True, 119.999)])
def test_missing_default_or_fresh_does_not_write_fence(db, fence_missing, age):
    result = db.expire_buy_order("buy-1", created_ts=CREATED.isoformat(),
                                 fence_missing=fence_missing,
                                 clock=lambda: CREATED + timedelta(seconds=age))
    assert result["state"] == "missing" and result["order"] is None
    assert buy_terminal(db) is None
    unchanged_accounting(db)


def test_missing_fence_is_sticky_for_repeated_fresh_or_invalid_calls(db):
    first = db.expire_buy_order("buy-1", created_ts=CREATED.isoformat(), fence_missing=True,
                                 clock=lambda: CREATED + timedelta(seconds=120))
    terminal = buy_terminal(db)
    for clock in (lambda: CREATED, lambda: 1 / 0):
        assert db.expire_buy_order("buy-1", created_ts="bad", clock=clock) == first
    assert buy_terminal(db) == terminal
    order = insert(db)
    result = db.expire_buy_order("buy-1", clock=lambda: CREATED)
    assert result["state"] == "expired" and result["order"]["order_id"] == order["order_id"]
    assert buy_terminal(db) == terminal
    unchanged_accounting(db)


def test_filled_order_wins_before_missing_fence_attempt(db):
    order = insert(db)
    assert fill(db, order)["ok"]
    receipt = db.expire_buy_order("buy-1", created_ts="bad", fence_missing=True,
                                  clock=lambda: 1 / 0)
    assert receipt["state"] == "filled"
    assert buy_terminal(db) is None
    assert len(db.list_fills()) == 1
    assert fill(db, order, clock=lambda: 1 / 0)["idempotent"]


@pytest.mark.parametrize("legacy", [True, False])
def test_older_valid_queue_origin_persists_restart_deadline_and_other_meta(db, legacy):
    later = (CREATED + timedelta(seconds=60)).isoformat()
    original_meta = {"retained": {"identity": ["exact", 2, False]}}
    if not legacy:
        original_meta[PAPER_BUY_CREATED_TS] = later
    order = insert(db, legacy=later, meta=original_meta)
    receipt = db.expire_buy_order("buy-1", created_ts=CREATED,
                                  clock=lambda: CREATED + timedelta(seconds=90))
    assert receipt["state"] == "new"
    stored = db.get_order_by_order_id(order["order_id"])
    expected = {**original_meta, PAPER_BUY_CREATED_TS: CREATED.isoformat()}
    assert stored["meta"] == expected and receipt["order"] == stored
    assert {key: value for key, value in stored.items() if key != "meta"} == {
        key: value for key, value in order.items() if key != "meta"}
    assert buy_terminal(db) is None
    restarted = store.PaperTradingSQLite()
    result = fill(restarted, order, clock=lambda: CREATED + timedelta(seconds=120))
    assert result["reason"] == "paper_buy_ttl:expired"
    assert buy_terminal(restarted)["state"] == "expired"
    unchanged_accounting(restarted)


@pytest.mark.parametrize("legacy", [True, False])
def test_later_queue_origin_never_overwrites_earlier_stored_origin(db, legacy):
    meta = {"keep": 1} if legacy else {PAPER_BUY_CREATED_TS: CREATED.isoformat(), "keep": 1}
    order = insert(db, legacy=CREATED.isoformat(), meta=meta)
    result = db.expire_buy_order("buy-1", created_ts=(CREATED + timedelta(seconds=20)).isoformat(),
                                 clock=lambda: CREATED + timedelta(seconds=30))
    assert result["state"] == "new" and result["order"] == order
    assert db.get_order_by_order_id(order["order_id"]) == order


@pytest.mark.parametrize("operation", ["fill", "expire"])
def test_existing_bad_age_commits_order_and_fence_together(db, operation):
    order = insert(db)
    clock = lambda: CREATED + timedelta(seconds=120)
    if operation == "fill":
        assert not fill(db, order, clock=clock)["ok"]
    else:
        assert db.expire_buy_order("buy-1", created_ts=CREATED.isoformat(), clock=clock)["state"] == "expired"
    terminal = buy_terminal(db)
    assert terminal["state"] == "expired" and terminal["reason"] == "paper_buy_ttl:expired"
    stored = db.get_order_by_order_id(order["order_id"])
    assert stored["status"] == terminal["state"] and stored["reject_reason"] == terminal["reason"]
    unchanged_accounting(db)


@pytest.mark.parametrize("operation", ["missing", "existing", "fill"])
def test_fence_write_failure_rolls_back_order_and_tombstone(db, monkeypatch, operation):
    order = insert(db) if operation != "missing" else None
    original = db._set_state_conn

    def fail_after_fence(con, key, value):
        original(con, key, value)
        if key.startswith("paper_buy_terminal:"):
            raise RuntimeError("fence write failure")

    monkeypatch.setattr(db, "_set_state_conn", fail_after_fence)
    with pytest.raises(RuntimeError, match="fence write failure"):
        clock = lambda: CREATED + timedelta(seconds=120)
        if operation == "fill":
            fill(db, order, clock=clock)
        else:
            db.expire_buy_order("buy-1", created_ts=CREATED.isoformat(), clock=clock, fence_missing=True)
    assert buy_terminal(db) is None
    assert db.get_order_by_client_id("buy-1") == order
    unchanged_accounting(db)


def test_missing_fence_serializes_with_late_insert_and_fill(db):
    inside_lock = threading.Event()
    release = threading.Event()
    inserting = threading.Event()

    def blocked_clock():
        inside_lock.set()
        assert release.wait(3)
        return CREATED + timedelta(seconds=120)

    def late_fill():
        inserting.set()
        order = insert(db, origin=(CREATED + timedelta(seconds=120)).isoformat())
        return fill(db, order, clock=lambda: CREATED + timedelta(seconds=121))

    with ThreadPoolExecutor(max_workers=2) as pool:
        expiry = pool.submit(db.expire_buy_order, "buy-1", created_ts=CREATED,
                             clock=blocked_clock, fence_missing=True)
        assert inside_lock.wait(3)
        late = pool.submit(late_fill)
        assert inserting.wait(3)
        release.set()
        assert expiry.result(timeout=5)["state"] == "expired"
        assert late.result(timeout=5)["reason"] == "paper_buy_ttl:expired"
    assert buy_terminal(db)["state"] == "expired"
    unchanged_accounting(db)


def test_fill_commits_before_waiting_missing_fence_and_wins(db):
    order = insert(db)
    inside_lock = threading.Event()
    release = threading.Event()

    def blocked_clock():
        inside_lock.set()
        assert release.wait(3)
        return CREATED + timedelta(seconds=119)

    with ThreadPoolExecutor(max_workers=2) as pool:
        filling = pool.submit(fill, db, order, clock=blocked_clock)
        assert inside_lock.wait(3)
        expiry = pool.submit(db.expire_buy_order, "buy-1", created_ts=CREATED,
                             clock=lambda: CREATED + timedelta(seconds=120), fence_missing=True)
        release.set()
        assert filling.result(timeout=5)["ok"]
        assert expiry.result(timeout=5)["state"] == "filled"
    assert buy_terminal(db) is None
    assert len(db.list_fills()) == 1
    assert float(db.get_state("cash_quote")) == 899


def test_buy_fence_does_not_affect_canonical_sell(db):
    db.expire_buy_order("buy-1", created_ts=CREATED, fence_missing=True,
                        clock=lambda: CREATED + timedelta(seconds=120))
    terminal = buy_terminal(db)
    db.upsert_position("BTC/USD", 1.0, 100.0, 0.0)
    order = insert(db, side="sell", origin="bad")
    assert db.expire_buy_order("buy-1", clock=lambda: 1 / 0)["state"] == "new"
    assert fill(db, order, clock=lambda: 1 / 0)["ok"]
    assert buy_terminal(db) == terminal


@pytest.mark.parametrize("raw", ['{', '{}', '{"state":"filled"}',
                                 '{"state":"expired","reason":"expired","client_order_id":"other"}',
                                 '{"state":[],"reason":"expired","client_order_id":"buy-1"}'])
def test_corrupt_buy_fence_fails_closed_without_rewrite(db, raw):
    db.set_state("paper_buy_terminal:buy-1", raw)
    order = insert(db)
    result = fill(db, order)
    assert not result["ok"] and result["reason"] == "invalid_buy_terminal"
    assert db.get_order_by_order_id(order["order_id"])["status"] == "rejected"
    assert db.get_state("paper_buy_terminal:buy-1") == raw
    unchanged_accounting(db)


@pytest.mark.parametrize("change", [
    {"venue": "other"}, {"symbol": "ETH/USD"}, {"side": "sell"}, {"qty": 2.0},
    {"order_type": "limit"}, {"limit_price": 100.0}, {"linked_order_id": "other-order"},
    {"qty": True},
])
def test_expected_identity_mismatch_blocks_before_any_mutation(db, change):
    order = insert(db)
    expected = {**order, **change}
    receipt = db.expire_buy_order("buy-1", created_ts=CREATED, expected_order=expected,
                                  fence_missing=True, clock=lambda: CREATED + timedelta(seconds=120))
    assert receipt == {"state": "blocked", "reason": "paper_buy_order_identity_mismatch", "order": order}
    assert db.get_order_by_order_id(order["order_id"]) == order
    assert buy_terminal(db) is None
    unchanged_accounting(db)


def test_expected_identity_accepts_normalization_and_ignores_strategy_id(db):
    order = insert(db)
    expected = {**order, "venue": " Coinbase ", "symbol": " BTC/USD ", "side": " BUY ",
                "order_type": " MARKET ", "linked_order_id": order["order_id"],
                "strategy_id": "legacy-fallback-is-not-identity"}
    receipt = db.expire_buy_order("buy-1", created_ts=CREATED, expected_order=expected,
                                  clock=lambda: CREATED + timedelta(seconds=30))
    assert receipt["state"] == "new" and receipt["order"] == order
    assert buy_terminal(db) is None


def test_expected_identity_does_not_mutate_wrong_order_appearing_after_initial_missing_read(db, monkeypatch):
    assert db.get_order_by_client_id("buy-1") is None
    expected = dict(venue="coinbase", symbol="BTC/USD", side="buy", qty=1.0,
                    order_type="market", limit_price=None)
    locked = threading.Event()
    original_connect = store._connect
    writer = original_connect()
    writer.execute("BEGIN IMMEDIATE")

    def connect():
        con = original_connect()
        locked.set()
        return con

    monkeypatch.setattr(store, "_connect", connect)
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            expiry = pool.submit(db.expire_buy_order, "buy-1", created_ts=CREATED,
                                 clock=lambda: CREATED + timedelta(seconds=120),
                                 fence_missing=True, expected_order=expected)
            assert locked.wait(3)
            writer.execute(
                "INSERT INTO paper_orders(order_id,client_order_id,created_ts,ts,venue,symbol,side,"
                "order_type,qty,status,meta_json) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                ("wrong-order", "buy-1", CREATED.isoformat(), CREATED.isoformat(), "coinbase",
                 "ETH/USD", "buy", "market", 1.0, "new", "{}"),
            )
            writer.execute("COMMIT")
            receipt = expiry.result(timeout=5)
    finally:
        writer.close()
    assert receipt["state"] == "blocked" and receipt["reason"] == "paper_buy_order_identity_mismatch"
    canonical = db.get_order_by_client_id("buy-1")
    assert canonical["order_id"] == "wrong-order" and canonical["status"] == "new"
    assert canonical["meta"] == {} and buy_terminal(db) is None
    unchanged_accounting(db)


@pytest.mark.parametrize("operation", ["fill", "expire"])
@pytest.mark.parametrize("age", [119.999, 120])
def test_legacy_open_buy_is_active_and_obeys_same_ttl(db, operation, age):
    order = insert(db, status="open")
    clock = lambda: CREATED + timedelta(seconds=age)
    if operation == "fill":
        receipt = fill(db, order, clock=clock)
        assert receipt["ok"] is (age < 120)
    else:
        receipt = db.expire_buy_order("buy-1", clock=clock)
        assert receipt["state"] == ("open" if age < 120 else "expired")
    canonical = db.get_order_by_order_id(order["order_id"])
    if age >= 120:
        assert receipt["reason"] == "paper_buy_ttl:expired"
        assert canonical["status"] == "expired"
        assert canonical["reject_reason"] == "paper_buy_ttl:expired"
        assert buy_terminal(db)["state"] == "expired"
        unchanged_accounting(db)
    elif operation == "fill":
        assert canonical["status"] == "filled"
        assert len(db.list_fills()) == 1
        assert float(db.get_state("cash_quote")) == 899
    else:
        assert canonical == order and buy_terminal(db) is None
        unchanged_accounting(db)


def queue_origin(*, client="buy-1", intent_id="queue-1", created=CREATED.isoformat()):
    path = store.DB_PATH.parent / "intent_queue.sqlite"
    with sqlite3.connect(path) as con:
        con.execute("CREATE TABLE IF NOT EXISTS trade_intents "
                    "(intent_id TEXT PRIMARY KEY, client_order_id TEXT, created_ts TEXT)")
        con.execute("INSERT INTO trade_intents(intent_id,client_order_id,created_ts) VALUES(?,?,?)",
                    (intent_id, client, created))
    return path


@pytest.mark.parametrize("operation", ["fill", "expire"])
@pytest.mark.parametrize("reserved_meta", [False, True])
def test_authoritative_queue_age_blocks_custom_legacy_client_after_origin_write_failure(db, operation, reserved_meta):
    queue_origin(client="legacy-custom")
    later = (CREATED + timedelta(seconds=110)).isoformat()
    meta = {PAPER_BUY_CREATED_TS: later, "retained": "identity"} if reserved_meta else None
    order = insert(db, client_order_id="legacy-custom", meta=meta, legacy=later)
    with sqlite3.connect(store.DB_PATH) as con:
        con.execute("CREATE TRIGGER fail_origin BEFORE UPDATE OF meta_json ON paper_orders "
                    "BEGIN SELECT RAISE(ABORT, 'transient_origin_failure'); END")
    with pytest.raises(sqlite3.IntegrityError, match="transient_origin_failure"):
        db.expire_buy_order("legacy-custom", created_ts=CREATED,
                            clock=lambda: CREATED + timedelta(seconds=110))
    assert db.get_order_by_order_id(order["order_id"]) == order
    with sqlite3.connect(store.DB_PATH) as con:
        con.execute("DROP TRIGGER fail_origin")
    restarted = store.PaperTradingSQLite()
    clock = lambda: CREATED + timedelta(seconds=121)
    if operation == "fill":
        result = fill(restarted, order, clock=clock)
        assert not result["ok"]
    else:
        result = restarted.expire_buy_order("legacy-custom", clock=clock)
        assert result["state"] == "expired"
    assert result["reason"] == "paper_buy_ttl:expired"
    assert restarted.get_order_by_order_id(order["order_id"])["status"] == "expired"
    unchanged_accounting(restarted)


@pytest.mark.parametrize("operation", ["fill", "expire"])
@pytest.mark.parametrize("queue_exists", [False, True])
def test_canonical_missing_queue_origin_stays_unresolved_without_creating_queue(db, operation, queue_exists):
    if queue_exists:
        queue_origin(client="unrelated", intent_id="unrelated")
    order = insert(db, client_order_id="paper_intent_unwritten")
    path = store.DB_PATH.parent / "intent_queue.sqlite"
    if operation == "fill":
        result = fill(db, order)
        assert not result["ok"]
    else:
        result = db.expire_buy_order(order["client_order_id"], clock=lambda: CREATED)
        assert result["state"] == "blocked"
    assert result["reason"] == "paper_buy_queue_origin_missing"
    assert path.exists() is queue_exists
    assert db.get_order_by_order_id(order["order_id"]) == order
    assert buy_terminal(db, order["client_order_id"]) is None
    unchanged_accounting(db)


@pytest.mark.parametrize("client,queued_client", [("paper_intent_queue-1", None), ("custom-legacy", "custom-legacy")])
def test_fresh_queue_origin_resolves_canonical_id_or_custom_client(db, client, queued_client):
    queue_origin(client=queued_client)
    order = insert(db, client_order_id=client)
    assert fill(db, order)["ok"]


@pytest.mark.parametrize("operation", ["fill", "expire"])
@pytest.mark.parametrize("client", ["paper_intent_queue-1", "custom-legacy"])
@pytest.mark.parametrize("damage", ["corrupt", "schema", "locked"])
def test_existing_unreadable_queue_blocks_all_active_buys_without_terminalizing(db, operation, client, damage):
    path = queue_origin(client=client)
    lock = None
    with sqlite3.connect(path) as con:
        if damage == "corrupt":
            con.execute("PRAGMA writable_schema=ON")
            con.execute("UPDATE sqlite_master SET sql='not valid sql' WHERE name='trade_intents'")
        elif damage == "schema":
            con.execute("DROP TABLE trade_intents")
    if damage == "locked":
        lock = sqlite3.connect(path)
        lock.execute("BEGIN EXCLUSIVE")
    order = insert(db, client_order_id=client, status="open")
    try:
        if operation == "fill":
            result = fill(db, order)
            assert not result["ok"]
        else:
            result = db.expire_buy_order(client, clock=lambda: CREATED)
            assert result["state"] == "blocked"
    finally:
        if lock is not None:
            lock.rollback()
            lock.close()
    assert result["reason"] == "paper_buy_queue_origin_unreadable"
    assert db.get_order_by_order_id(order["order_id"]) == order
    assert buy_terminal(db, client) is None
    unchanged_accounting(db)


@pytest.mark.parametrize("operation", ["fill", "expire"])
@pytest.mark.parametrize("created,reason", [(None, "missing_created_ts"), ("bad", "invalid_created_ts"),
                                           ((CREATED + timedelta(seconds=31)).isoformat(), "future_created_ts")])
def test_known_bad_queue_origin_cannot_hide_behind_fresh_metadata(db, operation, created, reason):
    queue_origin(created=created)
    order = insert(db)
    if operation == "fill":
        result = fill(db, order)
        assert not result["ok"]
    else:
        result = db.expire_buy_order("buy-1", clock=lambda: CREATED + timedelta(seconds=30))
        assert result["state"] == "rejected"
    assert result["reason"] == "paper_buy_ttl:" + reason
    assert db.get_order_by_order_id(order["order_id"])["status"] == "rejected"
    unchanged_accounting(db)


@pytest.mark.parametrize("second_origin,reason", [(CREATED.isoformat(), "expired"),
                                                ("bad", "invalid_created_ts"),
                                                ((CREATED + timedelta(seconds=121)).isoformat(), "future_created_ts")])
def test_multiple_queue_matches_never_ignore_older_or_invalid_origin(db, second_origin, reason):
    later = (CREATED + timedelta(seconds=110)).isoformat()
    queue_origin(intent_id="newer", created=later)
    queue_origin(intent_id="older-or-invalid", created=second_origin)
    order = insert(db, origin=later)
    result = fill(db, order, clock=lambda: CREATED + timedelta(seconds=120))
    assert not result["ok"] and result["reason"] == "paper_buy_ttl:" + reason
    unchanged_accounting(db)


def test_noncanonical_direct_order_with_unmatched_existing_queue_retains_own_age(db):
    queue_origin(client="unrelated", created="bad")
    order = insert(db)
    assert fill(db, order)["ok"]


@pytest.mark.parametrize("status", ["filled", "expired", "rejected", "canceled", "cancelled", "superseded"])
def test_terminal_order_does_not_depend_on_readable_queue(db, status):
    path = queue_origin()
    with sqlite3.connect(path) as con:
        con.execute("DROP TABLE trade_intents")
    order = insert(db, status=status)
    result = db.expire_buy_order("buy-1", clock=lambda: 1 / 0)
    assert result["state"] == status and result["order"] == order
    result = fill(db, order, clock=lambda: 1 / 0)
    assert result["ok"] is (status == "filled")
    assert db.get_order_by_order_id(order["order_id"]) == order


def test_existing_fence_precedes_queue_lookup_and_sells_ignore_unreadable_queue(db):
    db.expire_buy_order("buy-1", created_ts=CREATED, fence_missing=True,
                        clock=lambda: CREATED + timedelta(seconds=120))
    path = queue_origin()
    with sqlite3.connect(path) as con:
        con.execute("DROP TABLE trade_intents")
    order = insert(db)
    assert fill(db, order)["reason"] == "paper_buy_ttl:expired"
    sell = insert(db, side="sell", client_order_id="sell-1", order_id="sell-1", origin="bad")
    db.upsert_position("BTC/USD", 1, 100, 0)
    assert fill(db, sell, clock=lambda: 1 / 0)["ok"]


def test_queue_lookup_is_readonly_path_quoted_and_after_paper_write_lock(db, monkeypatch):
    quoted_parent = store.DB_PATH.parent / "space #?% directory"
    quoted_parent.mkdir()
    monkeypatch.setattr(store, "DB_PATH", quoted_parent / "paper.sqlite")
    isolated = store.PaperTradingSQLite()
    isolated.set_state("cash_quote", "1000")
    isolated.set_state("realized_pnl", "0")
    path = queue_origin()
    before = path.read_bytes()
    order = insert(isolated)
    original_connect = sqlite3.connect
    seen = []

    def connect(database, *args, **kwargs):
        if kwargs.get("uri"):
            seen.append(database)
            assert str(database).endswith("?mode=ro")
            assert "#" not in str(database) and "%23%3F%25" in str(database)
            assert 0 < kwargs["timeout"] <= 1
            with original_connect(store.DB_PATH, timeout=0) as writer:
                with pytest.raises(sqlite3.OperationalError, match="locked"):
                    writer.execute("BEGIN IMMEDIATE")
            con = original_connect(database, *args, **kwargs)
            with pytest.raises(sqlite3.OperationalError, match="readonly"):
                con.execute("DELETE FROM trade_intents")
            return con
        return original_connect(database, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", connect)
    assert fill(isolated, order)["ok"]
    assert len(seen) == 1 and path.read_bytes() == before
