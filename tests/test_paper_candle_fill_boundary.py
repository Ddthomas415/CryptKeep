from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import copy
import json
import sqlite3
import threading

import pytest

from services.execution.paper_buy_policy import PAPER_BUY_CREATED_TS
from services.market_data import hourly_candle_quality as quality
from storage import paper_trading_sqlite as store


CREATED = datetime(2026, 11, 4, 1, 0, tzinfo=timezone.utc)


@pytest.fixture
def db(monkeypatch, tmp_path):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "account-a" / "paper.sqlite")
    result = store.PaperTradingSQLite()
    result.initialize_account(1000, "USD")
    return result


def order(db, **changes):
    row = dict(order_id="order", client_order_id="direct-buy", venue="coinbase", symbol="BTC/USD",
               side="buy", order_type="market", qty=1, status="new", ts=CREATED.isoformat(),
               meta={PAPER_BUY_CREATED_TS: CREATED.isoformat()})
    row.update(changes)
    db.insert_order(row)
    return db.get_order_by_client_id(row["client_order_id"])


def fill(db, row, **changes):
    args = dict(order=row, ts=CREATED.isoformat(), price=100, qty=1, fee=0.5, fee_currency="USD",
                clock=lambda: CREATED + timedelta(seconds=30), hourly_candle_guard=True)
    args.update(changes)
    return db.apply_fill(**args)


def evidence(db, oid="order"):
    raw = db.get_state("paper_candle_check:" + oid)
    return json.loads(raw) if raw is not None else None


def no_accounting(db):
    assert db.list_fills() == [] and db.list_positions() == []
    assert db.get_state("cash_quote") == "1000.0" and db.get_state("realized_pnl") == "0.0"


def mock_quality(monkeypatch, verdict):
    calls = []

    def check(venue, symbol, *, clock, data_root):
        calls.append((venue, symbol, data_root, clock()))
        return copy.deepcopy(verdict)

    monkeypatch.setattr(quality, "check_cached_hourly_candles", check)
    return calls


@pytest.mark.parametrize("status", ["new", "open"])
@pytest.mark.parametrize("reason,ok", [("fresh", True), ("current_hour_stale", False), ("missing_hours", False)])
def test_active_buy_checks_and_commits_diagnostics(db, monkeypatch, status, reason, ok):
    verdict = {"ok": ok, "reason": reason, "missing_hours": [] if ok else [123], "policy_version": 1}
    calls = mock_quality(monkeypatch, verdict)
    row = order(db, status=status)
    result = fill(db, row)
    assert result["ok"] is ok and len(calls) == 1
    assert evidence(db) == verdict
    canonical = db.get_order_by_order_id(row["order_id"])
    assert canonical["status"] == ("filled" if ok else "rejected")
    if ok:
        assert len(db.list_fills()) == 1 and float(db.get_state("cash_quote")) == 899.5
    else:
        assert result["reason"] == canonical["reject_reason"] == "candle_data:" + reason
        assert result["candle_quality"] == verdict
        no_accounting(db)


def test_canonical_market_and_account_namespace_ignore_caller_and_environment(db, monkeypatch):
    calls = mock_quality(monkeypatch, {"ok": True, "reason": "fresh"})
    row = order(db)
    forged = {**row, "venue": "other-venue", "symbol": "ETH/USD", "side": "sell"}
    monkeypatch.setenv("CBP_STATE_DIR", str(store.DB_PATH.parent / "different-account"))
    assert fill(db, forged)["ok"]
    assert calls[0][:3] == ("coinbase", "BTC/USD", store.DB_PATH.parent)
    assert db.get_position("BTC/USD")["qty"] == 1 and db.get_position("ETH/USD") is None


@pytest.mark.parametrize("flag", [False, True, None, 1, "true", {}])
def test_sell_ignores_policy_and_never_reads_candles(db, monkeypatch, flag):
    def forbidden(*args, **kwargs):
        pytest.fail("sell must not read candles")

    monkeypatch.setattr(quality, "check_cached_hourly_candles", forbidden)
    db.upsert_position("BTC/USD", 1, 100, 0)
    row = order(db, side="sell", meta=None)
    assert fill(db, row, hourly_candle_guard=flag)["ok"]
    assert evidence(db) is None and db.get_position("BTC/USD")["qty"] == 0


def test_false_default_does_not_read_or_record_candles(db, monkeypatch):
    calls = mock_quality(monkeypatch, {"ok": False, "reason": "current_hour_stale"})
    row = order(db)
    assert db.apply_fill(order=row, ts=CREATED.isoformat(), price=100, qty=1, fee=0.5,
                         fee_currency="USD", clock=lambda: CREATED + timedelta(seconds=30))["ok"]
    assert calls == [] and evidence(db) is None


@pytest.mark.parametrize("flag", [None, 0, 1, 0.0, 1.0, "false", "true", [], {}])
def test_nonboolean_policy_rejects_buy_without_cache_read(db, monkeypatch, flag):
    calls = mock_quality(monkeypatch, {"ok": True, "reason": "fresh"})
    row = order(db)
    result = fill(db, row, hourly_candle_guard=flag)
    assert not result["ok"] and result["reason"] == "candle_data:invalid_policy"
    assert db.get_order_by_order_id(row["order_id"])["status"] == "rejected"
    assert evidence(db) == {"ok": False, "reason": "invalid_policy"} and calls == []
    no_accounting(db)


@pytest.mark.parametrize("status", ["filled", "expired", "rejected", "canceled", "cancelled", "superseded"])
def test_terminal_precedence_never_reads_or_overwrites_evidence(db, monkeypatch, status):
    calls = mock_quality(monkeypatch, {"ok": False, "reason": "current_hour_stale"})
    row = order(db, status=status)
    db.set_state("paper_candle_check:order", '{"earlier":"unchanged"}')
    result = fill(db, row, hourly_candle_guard="invalid", clock=lambda: 1 / 0)
    assert result["ok"] is (status == "filled")
    assert calls == [] and evidence(db) == {"earlier": "unchanged"}
    assert db.get_order_by_order_id(row["order_id"]) == row
    no_accounting(db)


def test_missing_order_and_existing_buy_fence_precede_candle_check(db, monkeypatch):
    calls = mock_quality(monkeypatch, {"ok": True, "reason": "fresh"})
    assert fill(db, {"order_id": "absent"})["reason"] == "order_not_found"
    db.expire_buy_order("direct-buy", created_ts=CREATED, fence_missing=True,
                        clock=lambda: CREATED + timedelta(seconds=120))
    row = order(db)
    assert fill(db, row)["reason"] == "paper_buy_ttl:expired"
    assert calls == [] and evidence(db) is None
    no_accounting(db)


@pytest.mark.parametrize("quality_ok", [True, False])
def test_ttl_is_sampled_after_helper_and_wins_over_bad_candles(db, monkeypatch, quality_ok):
    row = order(db)
    now = [CREATED + timedelta(seconds=119)]

    def check(venue, symbol, *, clock, data_root):
        assert clock() == now[0]
        now[0] = CREATED + timedelta(seconds=120)
        return {"ok": quality_ok, "reason": "fresh" if quality_ok else "current_hour_stale"}

    monkeypatch.setattr(quality, "check_cached_hourly_candles", check)
    result = fill(db, row, clock=lambda: now[0])
    assert result["reason"] == "paper_buy_ttl:expired"
    assert db.get_order_by_order_id(row["order_id"])["status"] == "expired"
    assert evidence(db) is None
    no_accounting(db)


@pytest.mark.parametrize("initial_age", [119, 120])
@pytest.mark.parametrize("quality_ok", [True, False])
def test_expiry_wins_over_selectively_unwritable_candle_evidence(db, monkeypatch, initial_age, quality_ok):
    row = order(db)
    now = [CREATED + timedelta(seconds=initial_age)]
    calls = []
    with sqlite3.connect(store.DB_PATH) as con:
        con.execute("CREATE TRIGGER fail_candle_evidence BEFORE INSERT ON paper_state "
                    "WHEN NEW.k='paper_candle_check:order' "
                    "BEGIN SELECT RAISE(ABORT, 'candle evidence unavailable'); END")

    def check(venue, symbol, *, clock, data_root):
        calls.append(clock())
        now[0] = CREATED + timedelta(seconds=120)
        return {"ok": quality_ok, "reason": "fresh" if quality_ok else "current_hour_stale"}

    monkeypatch.setattr(quality, "check_cached_hourly_candles", check)
    result = fill(db, row, clock=lambda: now[0])
    assert result == {"ok": False, "reason": "paper_buy_ttl:expired"}
    assert calls == [CREATED + timedelta(seconds=initial_age)]
    canonical = db.get_order_by_order_id(row["order_id"])
    assert canonical["status"] == "expired" and canonical["reject_reason"] == result["reason"]
    terminal = json.loads(db.get_state("paper_buy_terminal:direct-buy"))
    assert terminal["state"] == "expired" and terminal["reason"] == result["reason"]
    assert evidence(db) is None
    no_accounting(db)


def test_waiting_fill_reads_cache_update_only_after_write_lock(db, monkeypatch):
    row = order(db)
    waiting = threading.Event()
    called = threading.Event()
    cached = [{"ok": True, "reason": "fresh"}]
    original_connect = store._connect
    writer = original_connect()
    writer.execute("BEGIN IMMEDIATE")

    def connect():
        con = original_connect()
        waiting.set()
        return con

    def check(venue, symbol, *, clock, data_root):
        called.set()
        with sqlite3.connect(store.DB_PATH, timeout=0) as competing:
            with pytest.raises(sqlite3.OperationalError, match="locked"):
                competing.execute("BEGIN IMMEDIATE")
        return cached[0]

    monkeypatch.setattr(store, "_connect", connect)
    monkeypatch.setattr(quality, "check_cached_hourly_candles", check)
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(fill, db, row)
            assert waiting.wait(3) and not called.is_set()
            cached[0] = {"ok": False, "reason": "missing_hours"}
            writer.execute("COMMIT")
            assert pending.result(timeout=5)["reason"] == "candle_data:missing_hours"
    finally:
        writer.close()
    assert called.is_set() and evidence(db) == cached[0]
    no_accounting(db)


@pytest.mark.parametrize("quality_ok", [True, False])
def test_evidence_write_failure_rolls_back_and_allows_next_order(db, monkeypatch, quality_ok):
    mock_quality(monkeypatch, {"ok": quality_ok, "reason": "fresh" if quality_ok else "current_hour_stale"})
    row = order(db)
    db.set_state("paper_candle_check:order", '{"earlier":"preserve"}')
    original = db._set_state_conn

    def fail(con, key, value):
        original(con, key, value)
        if key == "paper_candle_check:order":
            raise sqlite3.OperationalError("synthetic evidence failure")

    monkeypatch.setattr(db, "_set_state_conn", fail)
    result = fill(db, row)
    assert result == {"ok": False, "reason": "candle_data:evidence_unwritable", "unresolved": True}
    assert db.get_order_by_order_id(row["order_id"]) == row
    assert evidence(db) == {"earlier": "preserve"}
    assert db.get_state("paper_buy_terminal:direct-buy") is None
    no_accounting(db)
    next_order = order(db, order_id="next", client_order_id="next")
    assert fill(db, next_order, hourly_candle_guard=False)["ok"]


@pytest.mark.parametrize("value", [float("nan"), float("inf")])
def test_nonfinite_diagnostic_is_unwritable_not_a_terminal_refusal(db, monkeypatch, value):
    mock_quality(monkeypatch, {"ok": True, "reason": "fresh", "checked_epoch": value})
    row = order(db)
    assert fill(db, row) == {"ok": False, "reason": "candle_data:evidence_unwritable", "unresolved": True}
    assert db.get_order_by_order_id(row["order_id"]) == row
    assert evidence(db) is None
    no_accounting(db)


@pytest.mark.parametrize("malformed", [None, [], {"ok": 1, "reason": "fresh"}, {"ok": True}])
def test_malformed_helper_verdict_cannot_fill(db, monkeypatch, malformed):
    mock_quality(monkeypatch, malformed)
    row = order(db)
    assert fill(db, row)["reason"] == "candle_data:invalid_verdict"
    no_accounting(db)


def test_helper_exception_is_durable_refusal_not_uncaught(db, monkeypatch):
    def failing(*args, **kwargs):
        raise OSError("unreadable")

    monkeypatch.setattr(quality, "check_cached_hourly_candles", failing)
    row = order(db)
    assert fill(db, row)["reason"] == "candle_data:cache_unreadable"
    assert evidence(db) == {"ok": False, "reason": "cache_unreadable"}
    no_accounting(db)


@pytest.mark.parametrize("age_after_write", [119.999, 120, 121])
@pytest.mark.parametrize("quality_ok", [True, False])
def test_successful_diagnostic_write_rechecks_ttl_and_refreshes_fill_time(db, monkeypatch, age_after_write, quality_ok):
    verdict = {"ok": quality_ok, "reason": "fresh" if quality_ok else "current_hour_stale"}
    mock_quality(monkeypatch, verdict)
    row = order(db)
    now = [CREATED + timedelta(seconds=119)]
    original = db._set_state_conn

    def delayed_write(con, key, value):
        result = original(con, key, value)
        if key == "paper_candle_check:order":
            now[0] = CREATED + timedelta(seconds=age_after_write)
        return result

    monkeypatch.setattr(db, "_set_state_conn", delayed_write)
    result = fill(db, row, clock=lambda: now[0])
    canonical = db.get_order_by_order_id(row["order_id"])
    assert evidence(db) == verdict
    if age_after_write >= 120:
        assert result == {"ok": False, "reason": "paper_buy_ttl:expired"}
        assert canonical["status"] == "expired" and canonical["reject_reason"] == result["reason"]
        terminal = json.loads(db.get_state("paper_buy_terminal:direct-buy"))
        assert terminal["state"] == "expired" and terminal["reason"] == result["reason"]
        no_accounting(db)
    elif quality_ok:
        assert result["ok"] and canonical["status"] == "filled"
        assert db.list_fills()[0]["ts"] == now[0].isoformat()
        assert db.get_position("BTC/USD")["updated_ts"] == now[0].isoformat()
        assert float(db.get_state("cash_quote")) == 899.5
    else:
        assert result["reason"] == "candle_data:current_hour_stale" and canonical["status"] == "rejected"
        assert db.get_state("paper_buy_terminal:direct-buy") is None
        no_accounting(db)


def test_guarded_default_clock_records_post_diagnostic_fill_time(db, monkeypatch):
    mock_quality(monkeypatch, {"ok": True, "reason": "fresh"})
    row = order(db)
    now = [CREATED + timedelta(seconds=119)]
    original = db._set_state_conn

    class MutableDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return now[0]

    def delayed_write(con, key, value):
        result = original(con, key, value)
        if key == "paper_candle_check:order":
            now[0] = CREATED + timedelta(seconds=119.999)
        return result

    monkeypatch.setattr(store, "datetime", MutableDateTime)
    monkeypatch.setattr(db, "_set_state_conn", delayed_write)
    assert fill(db, row, clock=None)["ok"]
    assert db.list_fills()[0]["ts"] == now[0].isoformat()
    assert db.get_position("BTC/USD")["updated_ts"] == now[0].isoformat()
