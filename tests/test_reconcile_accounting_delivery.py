import sqlite3
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from types import SimpleNamespace

import pytest

from services.execution import _executor_reconcile as reconcile
from storage.execution_store_sqlite import ExecutionStore


@pytest.fixture
def rig(tmp_path, monkeypatch):
    db = str(tmp_path / "execution.sqlite")
    store = ExecutionStore(path=db)
    store.upsert_intent(dict(intent_id="intent", ts_ms=1, mode="live", exchange="coinbase",
        symbol="BTC/USD", side="buy", qty=1, status="submitted", reason="remote_id=order"))
    state = dict(order=dict(id="order", status="closed", filled=1, average=100,
                           fee=dict(cost=0, currency="USD")), trades=[], delivered=[], refused=False)
    cfg = SimpleNamespace(exec_db=db, exchange_id="coinbase", sandbox=True, symbol="BTC/USD",
        reconcile_limit=5, reconcile_trades=True, reconcile_lookback_ms=60000, reconcile_trades_limit=50)
    # Public facade tests synchronize mocks into this module; reset our store explicitly.
    monkeypatch.setattr(reconcile, "ExecutionStore", ExecutionStore)
    monkeypatch.setattr(reconcile, "_now_ms", lambda: 1700000060000)
    monkeypatch.setattr(reconcile, "_hard_off_guard", lambda *a, **kw: (True, "test"))
    monkeypatch.setattr(reconcile, "_load_execution_safety_cfg", lambda: None)
    monkeypatch.setattr(reconcile, "_latency_tracker", lambda _: SimpleNamespace(record_fill=lambda **kw: None))
    monkeypatch.setattr(reconcile, "_record_execution_metric", lambda **kw: None)
    monkeypatch.setattr(reconcile, "_is_live_shadow", lambda _: False)
    monkeypatch.setattr(reconcile, "ExchangeClient", lambda **kw: SimpleNamespace(fetch_my_trades=lambda: None))
    monkeypatch.setattr(reconcile, "_open_reconcile_session", lambda _: (object(), False))
    monkeypatch.setattr(reconcile, "_close_reconcile_session", lambda *a, **kw: None)
    monkeypatch.setattr(reconcile, "_fetch_order_for_reconcile", lambda *a, **kw: state["order"])
    monkeypatch.setattr(reconcile, "_fetch_trades_for_reconcile", lambda *a, **kw: state["trades"])
    monkeypatch.setattr(reconcile, "OrderDedupeStore", lambda **kw: SimpleNamespace(
        get_by_intent=lambda *a: {}, mark_terminal=lambda **kw: None))

    def sink(fill, **kw):
        state["delivered"].append(fill["fill_id"])
        return {"ok": not state["refused"]}

    monkeypatch.setattr(reconcile, "_on_fill", sink)
    return store, cfg, state


def trade(qty=1, fid="trade"):
    return dict(id=fid, order="order", side="buy", timestamp=1700000000000,
                amount=qty, price=100, fee=dict(cost=0, currency="USD"))


def status(store):
    with sqlite3.connect(store.path) as c:
        return c.execute("SELECT status FROM intents WHERE intent_id='intent'").fetchone()[0]


@pytest.mark.parametrize("remote_status", ["canceled", "cancelled", "rejected", "expired"])
@pytest.mark.parametrize("quantity", [None, "missing", "", "bad", float("nan"), float("inf"), -1, False])
def test_unknown_remote_quantity_cannot_terminalize(rig, remote_status, quantity):
    store, cfg, state = rig
    state["order"].update(status=remote_status, filled=quantity)
    if quantity == "missing":
        state["order"].pop("filled")
    out = reconcile.reconcile_live(cfg)
    assert out["ok"] is False
    assert out["accounting_incomplete"] == ["intent"]
    assert status(store) == "submitted"
    assert state["delivered"] == []


@pytest.mark.parametrize("remote_status", ["canceled", "cancelled", "rejected", "expired"])
@pytest.mark.parametrize("quantity", [0, "0"])
def test_explicit_zero_quantity_can_terminalize(rig, remote_status, quantity):
    store, cfg, state = rig
    state["order"].update(status=remote_status, filled=quantity)
    assert reconcile.reconcile_live(cfg)["ok"] is True
    assert status(store) == "canceled"
    assert state["delivered"] == []


def test_unknown_quantity_retries_when_explicit_evidence_arrives(rig):
    store, cfg, state = rig
    state["order"].update(status="canceled", filled=None)
    assert reconcile.reconcile_live(cfg)["ok"] is False
    assert status(store) == "submitted"
    state["order"]["filled"] = 0
    assert reconcile.reconcile_live(cfg)["ok"] is True
    assert status(store) == "canceled"


@pytest.mark.parametrize("trade_path", [True, False])
def test_competing_writer_does_not_abort_other_intents(rig, monkeypatch, trade_path):
    store, cfg, state = rig
    store.upsert_intent(dict(intent_id="other", ts_ms=2, mode="live", exchange="coinbase",
        symbol="BTC/USD", side="buy", qty=1, status="submitted", reason="remote_id=other-order"))
    monkeypatch.setattr(reconcile, "_list_intents_any", lambda *a, **kw: [
        dict(intent_id="intent", symbol="BTC/USD", side="buy", qty=1, reason="remote_id=order"),
        dict(intent_id="other", symbol="BTC/USD", side="buy", qty=1, reason="remote_id=other-order"),
    ])
    monkeypatch.setattr(reconcile, "_fetch_order_for_reconcile", lambda *a, **kw:
        dict(id="other-order", status="canceled", filled=0) if kw["order_id"] == "other-order"
        else state["order"])
    state["trades"] = [trade()] if trade_path else []
    original = ExecutionStore.add_fill
    raced = []

    def competing_write(self, **kwargs):
        if not raced:
            raced.append(True)
            original(self, intent_id="intent", ts_ms=1, price=100, qty=1, fee=0,
                fee_ccy="USD", meta={"trade_id": "winner"}, max_recorded_qty=1,
                canonical_fill=dict(venue="coinbase", fill_id="winner", symbol="BTC/USD",
                                    side="buy", qty=1, price=100, ts="1"))
        return original(self, **kwargs)

    monkeypatch.setattr(ExecutionStore, "add_fill", competing_write)
    out = reconcile.reconcile_live(cfg)
    assert out["ok"] is False
    assert out["accounting_incomplete"] == ["intent"]
    assert out["checked"] == 2
    assert out["fills_added"] == 0
    assert status(store) == "submitted"
    with sqlite3.connect(store.path) as c:
        assert c.execute("SELECT status FROM intents WHERE intent_id='other'").fetchone()[0] == "canceled"
    assert store.reconcile_fill_coverage(intent_id="intent")["qty"] == 1
    monkeypatch.setattr(ExecutionStore, "add_fill", original)
    state["trades"] = []
    assert reconcile.reconcile_live(cfg)["ok"] is True
    assert status(store) == "filled"
    assert state["delivered"] == ["winner"]


@pytest.mark.parametrize("remote_status", ["closed", "canceled"])
def test_failed_accounting_is_durable_and_retried_without_trade_history(rig, remote_status):
    store, cfg, state = rig
    state["order"].update(status=remote_status, filled=.4 if remote_status == "canceled" else 1)
    state["trades"] = [trade(state["order"]["filled"])]
    state["refused"] = True
    out = reconcile.reconcile_live(cfg)
    assert out["ok"] is False
    assert out["accounting_incomplete"] == ["intent"]
    assert status(store) == "submitted"
    assert len(ExecutionStore(path=store.path).pending_reconcile_fills(intent_id="intent")) == 1
    state["refused"] = False
    state["trades"] = []
    out = reconcile.reconcile_live(cfg)
    assert out["ok"] is True
    assert out["fills_added"] == 0
    assert status(store) == ("filled" if remote_status == "closed" else "canceled")
    assert store.reconcile_fill_coverage(intent_id="intent")["qty"] == state["order"]["filled"]


def test_partial_order_remains_tracked_and_incomplete_history_does_not_close(rig):
    store, cfg, state = rig
    state["order"].update(status="open", filled=.4)
    state["trades"] = [trade(.4)]
    assert reconcile.reconcile_live(cfg)["ok"] is True
    assert status(store) == "partially_filled"
    state["order"].update(status="closed", filled=1)
    assert reconcile.reconcile_live(cfg)["ok"] is False
    assert status(store) == "partially_filled"
    assert store.reconcile_fill_coverage(intent_id="intent")["qty"] == .4
    state["trades"] = []
    assert reconcile.reconcile_live(cfg)["ok"] is False
    assert store.reconcile_fill_coverage(intent_id="intent")["qty"] == .4
    state["trades"] = [trade(.6, "remainder")]
    assert reconcile.reconcile_live(cfg)["ok"] is True
    assert status(store) == "filled"


def test_synthetic_fill_delivery_is_durable(rig):
    store, cfg, state = rig
    state["refused"] = True
    assert reconcile.reconcile_live(cfg)["ok"] is False
    assert status(store) == "submitted"
    state["refused"] = False
    assert reconcile.reconcile_live(cfg)["ok"] is True
    assert store.reconcile_fill_coverage(intent_id="intent")["qty"] == 1
    assert state["delivered"] == ["order:order:closed", "order:order:closed"]


def test_legacy_recorded_fill_is_not_assumed_accounted(rig):
    store, cfg, state = rig
    store.add_fill(intent_id="intent", ts_ms=1, price=100, qty=1, fee=0, fee_ccy="USD",
                   meta={"trade_id": "legacy"})
    assert reconcile.reconcile_live(cfg)["ok"] is False
    assert status(store) == "submitted"
    assert state["delivered"] == []
    assert store.reconcile_fill_coverage(intent_id="intent")["qty"] == 1


def test_failed_completion_marker_keeps_delivery_for_restart(rig, monkeypatch):
    store, cfg, state = rig
    state["trades"] = [trade()]
    original = ExecutionStore.complete_reconcile_fill
    monkeypatch.setattr(ExecutionStore, "complete_reconcile_fill",
        lambda *a, **kw: (_ for _ in ()).throw(sqlite3.OperationalError("injected marker failure")))
    assert reconcile.reconcile_live(cfg)["ok"] is False
    assert status(store) == "submitted"
    assert len(store.pending_reconcile_fills(intent_id="intent")) == 1
    monkeypatch.setattr(ExecutionStore, "complete_reconcile_fill", original)
    state["trades"] = []
    assert reconcile.reconcile_live(cfg)["ok"] is True
    assert status(store) == "filled"


def test_fill_and_delivery_rollback_together(rig):
    store, _, _ = rig
    with sqlite3.connect(store.path) as c:
        c.execute("CREATE TRIGGER fail_fill BEFORE INSERT ON fills "
                  "BEGIN SELECT RAISE(ABORT, 'injected fill failure'); END")
    with pytest.raises(sqlite3.IntegrityError):
        store.add_fill(intent_id="intent", ts_ms=1, price=100, qty=1, fee=0, fee_ccy="USD",
            meta={"trade_id": "trade"}, canonical_fill=dict(venue="coinbase", fill_id="trade"))
    assert store.pending_reconcile_fills(intent_id="intent") == []
    assert store.reconcile_fill_coverage(intent_id="intent")["qty"] == 0


def test_unreadable_coverage_is_not_zero(rig, monkeypatch):
    store, cfg, state = rig
    monkeypatch.setattr(ExecutionStore, "reconcile_fill_coverage",
        lambda *a, **kw: (_ for _ in ()).throw(sqlite3.OperationalError("injected read failure")))
    assert reconcile.reconcile_live(cfg)["ok"] is False
    assert status(store) == "submitted"
    assert state["delivered"] == []


def test_retry_after_sink_commit_does_not_double_loss_counter(rig, monkeypatch, tmp_path):
    from services.journal import fill_sink
    store, cfg, state = rig
    monkeypatch.setattr(fill_sink, "data_dir", lambda: tmp_path)
    state["trades"] = [{**trade(), "realized_pnl_usd": -2}]
    sink = fill_sink.CanonicalFillSink(exec_db=store.path)
    monkeypatch.setattr(reconcile, "_on_fill", lambda fill, **kw: sink.on_fill(fill))
    original = ExecutionStore.complete_reconcile_fill
    calls = []

    def fail_once(self, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise sqlite3.OperationalError("failure after accounting commit")
        return original(self, **kwargs)

    monkeypatch.setattr(ExecutionStore, "complete_reconcile_fill", fail_once)
    assert reconcile.reconcile_live(cfg)["ok"] is False
    state["trades"] = []
    assert reconcile.reconcile_live(cfg)["ok"] is True
    with sqlite3.connect(store.path) as c:
        assert c.execute("SELECT loss_count FROM symbol_locks").fetchone()[0] == 1
        assert c.execute("SELECT COUNT(*) FROM canonical_fills").fetchone()[0] == 1
    assert status(store) == "filled"


@pytest.mark.parametrize("average", [None, "invalid", float("nan"), float("inf"), 0, -1])
def test_limit_price_is_not_execution_average(rig, average):
    store, cfg, state = rig
    state["order"].update(average=average, price=100)
    assert reconcile.reconcile_live(cfg)["ok"] is False
    assert status(store) == "submitted"
    assert state["delivered"] == []
    assert store.reconcile_fill_coverage(intent_id="intent")["qty"] == 0


def test_complete_trade_evidence_can_close_without_order_average(rig):
    store, cfg, state = rig
    state["order"].update(average=None, price=999)
    state["trades"] = [trade()]
    assert reconcile.reconcile_live(cfg)["ok"] is True
    assert status(store) == "filled"


def test_stale_synthetic_snapshot_cannot_over_record_quantity(rig):
    store, _, _ = rig
    store.add_fill(intent_id="intent", ts_ms=1, price=100, qty=.4, fee=0, fee_ccy="USD",
                   meta={"trade_id": "real-partial"})
    with pytest.raises(ValueError, match="exceed reported"):
        store.add_fill(intent_id="intent", ts_ms=2, price=100, qty=1, fee=0, fee_ccy="USD",
            meta={"trade_id": "synthetic"}, max_recorded_qty=1,
            canonical_fill=dict(venue="coinbase", fill_id="synthetic"))
    assert store.reconcile_fill_coverage(intent_id="intent")["qty"] == .4
    assert store.pending_reconcile_fills(intent_id="intent") == []


def test_late_real_trade_cannot_duplicate_synthetic_quantity(rig):
    store, _, _ = rig
    store.add_fill(intent_id="intent", ts_ms=1, price=100, qty=1, fee=0, fee_ccy="USD",
                   meta={"trade_id": "synthetic"}, max_recorded_qty=1)
    with pytest.raises(ValueError, match="exceed reported"):
        store.add_fill(intent_id="intent", ts_ms=2, price=100, qty=.4, fee=0, fee_ccy="USD",
                       meta={"trade_id": "real-partial"}, max_recorded_qty=1)
    assert store.reconcile_fill_coverage(intent_id="intent")["qty"] == 1


def test_competing_real_and_synthetic_writers_cannot_exceed_remote_total(rig):
    store, _, _ = rig
    barrier = Barrier(2)

    def write(fid, qty):
        barrier.wait(timeout=5)
        try:
            store.add_fill(intent_id="intent", ts_ms=1, price=100, qty=qty, fee=0,
                           fee_ccy="USD", meta={"trade_id": fid}, max_recorded_qty=1)
            return True
        except ValueError:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(write, "synthetic", 1)
        b = pool.submit(write, "real-partial", .4)
        assert sorted([a.result(timeout=10), b.result(timeout=10)]) == [False, True]
    assert store.reconcile_fill_coverage(intent_id="intent")["qty"] in {.4, 1}


def test_duplicate_fill_does_not_consume_quantity_twice(rig):
    store, _, _ = rig
    for _ in range(2):
        store.add_fill(intent_id="intent", ts_ms=1, price=100, qty=1, fee=0,
                       fee_ccy="USD", meta={"trade_id": "same"}, max_recorded_qty=1)
    assert store.reconcile_fill_coverage(intent_id="intent")["qty"] == 1
