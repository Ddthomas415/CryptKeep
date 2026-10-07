import sqlite3
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from storage.execution_store_sqlite import ExecutionStore
from services.journal import fill_sink


def apply(store, fid="loss", pnl=-1, venue="coinbase"):
    store.activate_symbol_loss_cutover()
    return store.apply_symbol_loss_fill_once(
        venue=venue, fill_id=fid, symbol="BTC/USD", realized_pnl_usd=pnl,
        loss_limit=3, lock_duration_ms=60000,
    )


def counters(path):
    with sqlite3.connect(path) as c:
        return c.execute("SELECT loss_count, locked_until_ms FROM symbol_locks").fetchone()


def test_delayed_profit_cannot_clear_newer_loss_lock(tmp_path, monkeypatch):
    path = str(tmp_path / "ordered.sqlite")
    monkeypatch.setattr(fill_sink, "data_dir", lambda: tmp_path)
    sink = fill_sink.CanonicalFillSink(exec_db=path)
    paused, resume = Event(), Event()
    original = ExecutionStore.apply_symbol_loss_fill_once

    def delay_profit(self, **kwargs):
        if kwargs["fill_id"] == "profit" and not resume.is_set():
            paused.set()
            assert resume.wait(timeout=5)
        return original(self, **kwargs)

    monkeypatch.setattr(ExecutionStore, "apply_symbol_loss_fill_once", delay_profit)
    def fill(fid, pnl):
        return dict(venue="coinbase", fill_id=fid, symbol="BTC/USD", side="sell",
                    qty=1, price=100, ts="1", fee_usd=0, realized_pnl_usd=pnl)
    with ThreadPoolExecutor(max_workers=1) as pool:
        profit = pool.submit(sink.on_fill, fill("profit", 2))
        try:
            assert paused.wait(timeout=5)
            for fid in ["loss1", "loss2", "loss3"]:
                assert sink.on_fill(fill(fid, -1))["ok"] is False
            assert counters(path) is None
        finally:
            resume.set()
        assert profit.result(timeout=5)["ok"] is True
    # Retry in deliberately wrong order after restart: no leapfrogging.
    restarted = fill_sink.CanonicalFillSink(exec_db=path)
    assert restarted.on_fill(fill("loss3", -1))["ok"] is False
    for fid in ["loss1", "loss2", "loss3"]:
        assert restarted.on_fill(fill(fid, -1))["ok"] is True
    lock = counters(path)
    assert lock[0] == 3 and lock[1] > 0
    assert restarted.on_fill(fill("profit", 2))["ok"] is True
    assert counters(path) == lock


def test_replay_and_restart_do_not_count_twice(tmp_path):
    path = str(tmp_path / "execution.sqlite")
    store = ExecutionStore(path=path)
    assert apply(store) == 1
    assert apply(ExecutionStore(path=path)) == 1
    assert counters(path)[0] == 1
    assert apply(store, "second") == 2
    assert apply(store, "third") == 3
    lock = counters(path)
    assert lock[1] > 0
    assert apply(store, "third") == 3
    assert counters(path) == lock


def test_profit_replay_does_not_erase_later_loss(tmp_path):
    store = ExecutionStore(path=str(tmp_path / "execution.sqlite"))
    apply(store)
    assert apply(store, "profit", 2) == 0
    apply(store, "later")
    assert apply(store, "profit", 2) == 0
    assert counters(store.path)[0] == 1


def test_concurrent_duplicate_is_applied_once(tmp_path):
    store = ExecutionStore(path=str(tmp_path / "execution.sqlite"))
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(lambda _: apply(store), range(12))) == [1] * 12
    assert counters(store.path)[0] == 1


def test_marker_failure_rolls_back_counter(tmp_path):
    store = ExecutionStore(path=str(tmp_path / "execution.sqlite"))
    with sqlite3.connect(store.path) as c:
        c.execute("CREATE TRIGGER fail_marker BEFORE INSERT ON symbol_loss_fill_events "
                  "BEGIN SELECT RAISE(ABORT, 'injected failure'); END")
    with pytest.raises(sqlite3.IntegrityError):
        apply(store)
    assert counters(store.path) is None
    with sqlite3.connect(store.path) as c:
        c.execute("DROP TRIGGER fail_marker")
    assert apply(store) == 1


def test_conflicting_replay_refused_and_venue_identity_preserved(tmp_path):
    store = ExecutionStore(path=str(tmp_path / "execution.sqlite"))
    apply(store)
    with pytest.raises(ValueError, match="conflicting"):
        apply(store, pnl=2)
    assert counters(store.path)[0] == 1
    assert apply(store, venue="kraken") == 2


@pytest.mark.parametrize("pnl", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_pnl_refused(tmp_path, pnl):
    store = ExecutionStore(path=str(tmp_path / "execution.sqlite"))
    with pytest.raises(ValueError):
        apply(store, pnl=pnl)
    assert counters(store.path) is None


def test_sink_retries_loss_update_after_daily_commit(tmp_path, monkeypatch):
    path = str(tmp_path / "execution.sqlite")
    monkeypatch.setattr(fill_sink, "data_dir", lambda: tmp_path)
    monkeypatch.setenv("CBP_SYMBOL_LOSS_LIMIT", "3")
    monkeypatch.setenv("CBP_SYMBOL_LOCK_MINUTES", "60")
    sink = fill_sink.CanonicalFillSink(exec_db=path)
    original = ExecutionStore.apply_symbol_loss_fill_once
    calls = []

    def failing_once(self, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise sqlite3.OperationalError("injected loss update failure")
        return original(self, **kwargs)

    monkeypatch.setattr(ExecutionStore, "apply_symbol_loss_fill_once", failing_once)
    fill = dict(venue="coinbase", fill_id="loss", symbol="BTC/USD", side="sell",
                qty=1, price=100, ts="1700000000000", fee_usd=1, realized_pnl_usd=-2)
    assert sink.on_fill(fill)["ok"] is False
    assert (tmp_path / "risk_sink_failed.flag").exists()
    assert sink.on_fill(fill)["ok"] is True
    assert sink.on_fill(fill)["ok"] is True
    assert counters(path)[0] == 1


def test_cutover_preserves_legacy_counters_and_excludes_old_replay(tmp_path):
    path = str(tmp_path / "execution.sqlite")
    journal = fill_sink.CanonicalJournal(exec_db=path)
    journal.record_fill(venue="coinbase", fill_id="old-loss", symbol="BTC/USD",
                        side="sell", qty=1, price=100, ts="old", realized_pnl_usd=-1)
    journal.record_fill(venue="coinbase", fill_id="old-profit", symbol="BTC/USD",
                        side="sell", qty=1, price=100, ts="old", realized_pnl_usd=2)
    store = ExecutionStore(path=path)
    store.set_symbol_lock("BTC/USD", 9999999999999, 2, "legacy")
    before = counters(path)
    boundary = store.activate_symbol_loss_cutover()
    assert counters(path) == before
    assert apply(store, "old-loss") == 2
    assert apply(store, "old-profit", 2) == 2
    assert counters(path) == before
    assert apply(store, "new-loss") == 3
    reopened = ExecutionStore(path=path)
    assert reopened.activate_symbol_loss_cutover() == boundary
    assert apply(reopened, "old-profit", 2) == 3
    assert counters(path)[0] == 3


def test_cutover_failure_does_not_publish_boundary(tmp_path):
    store = ExecutionStore(path=str(tmp_path / "execution.sqlite"))
    with sqlite3.connect(store.path) as c:
        c.execute("CREATE TABLE canonical_fills(venue TEXT)")
    with pytest.raises(sqlite3.OperationalError):
        store.activate_symbol_loss_cutover()
    with sqlite3.connect(store.path) as c:
        assert c.execute("SELECT COUNT(*) FROM symbol_loss_cutover").fetchone()[0] == 0


def test_side_effect_requires_explicit_cutover(tmp_path):
    store = ExecutionStore(path=str(tmp_path / "execution.sqlite"))
    with pytest.raises(RuntimeError, match="not activated"):
        store.apply_symbol_loss_fill_once(venue="coinbase", fill_id="new", symbol="BTC/USD",
            realized_pnl_usd=-1, loss_limit=3, lock_duration_ms=60000)
    assert counters(store.path) is None
