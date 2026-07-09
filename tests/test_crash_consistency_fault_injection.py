"""
Substrate backlog #4 (with #3 companion proof): crash-consistency fault
injection for the live submit, fill, reconcile, and restart paths.

Mechanism: a monkeypatched side effect raises SystemExit mid-sequence.
SystemExit escapes the consumer's `except Exception` submit handler, so the
error-recovery paths cannot soften the crash — persistent state at the kill
point is exactly what a process death would leave (module-level `finally`
blocks release the run lock, which a real crash also survives via the
stale-lock reclaim proven elsewhere). "Restart" is a fresh run against the
same real sqlite stores.

Invariants asserted per scenario:
- exactly-once venue submission per intent across all phases (the money
  invariant);
- fill accounting idempotent by trade_id/fill_id (no double PnL);
- queue status either converges to the correct terminal/settled state or
  strands in a documented-safe state, which the test pins explicitly.

Findings pinned here:
- crashes between dedupe claim/venue submit and the queue status write leave
  the intent at `submitting`; the dedupe guard prevents resubmission, and the
  consumer's startup stale-`submitting` recovery sweep converges the row from
  the venue's record without ever resubmitting;
- convergence-by-design: a crash after fill accounting but before the
  `filled` transition converges on the next pass via the reconciler's 60s
  cursor overlap re-fetch plus INSERT OR IGNORE idempotence in the trading
  store and canonical journal; the multi-fill edge beyond the overlap window
  converges via the canonical-journal accounted-fill lookback.
"""
from __future__ import annotations

import importlib
from datetime import datetime, timezone

import pytest


class _Kill(SystemExit):
    """Simulated hard process death at a specific side effect."""


# ---------------------------------------------------------------------------
# harness
# ---------------------------------------------------------------------------


def _reload_live_stack(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("CBP_EXECUTION_ARMED", "1")
    monkeypatch.setenv("CBP_LIVE_ENABLED", "1")

    import services.os.app_paths as app_paths
    import storage.live_intent_queue_sqlite as queue_mod
    import storage.live_trading_sqlite as trading_mod
    import storage.order_dedupe_store_sqlite as dedupe_mod
    import services.execution.live_intent_consumer as consumer
    import services.execution.live_reconciler as reconciler

    importlib.reload(app_paths)
    importlib.reload(queue_mod)
    importlib.reload(trading_mod)
    importlib.reload(dedupe_mod)
    importlib.reload(consumer)
    importlib.reload(reconciler)
    return queue_mod, trading_mod, dedupe_mod, consumer, reconciler


def _seed_intent(queue_mod, intent_id: str):
    qdb = queue_mod.LiveIntentQueueSQLite()
    qdb.upsert_intent({
        "intent_id": intent_id,
        "created_ts": datetime.now(timezone.utc).isoformat(),
        "ts": datetime.now(timezone.utc).isoformat(),
        "source": "strategy",
        "venue": "coinbase",
        "symbol": "BTC/USD",
        "side": "buy",
        "order_type": "limit",
        "qty": 0.5,
        "limit_price": 100.0,
        "status": "queued",
        "last_error": None,
        "client_order_id": f"cid-{intent_id}",
        "exchange_order_id": None,
    })
    return qdb


class _Venue:
    """Shared fake venue: remembers placed orders across process restarts."""

    def __init__(self):
        self.submits: list[dict] = []
        self.orders: dict[str, dict] = {}  # client_order_id -> order
        self.trades: list[dict] = []
        self.lookup_enabled = True

    def place(self, client_order_id: str) -> dict:
        order = {"id": f"ex-{client_order_id}", "clientOrderId": client_order_id, "status": "open"}
        self.orders[client_order_id] = order
        return order

    def close_with_trade(self, client_order_id: str, trade_id: str) -> None:
        order = self.orders[client_order_id]
        order["status"] = "closed"
        self.trades.append({
            "id": trade_id,
            "order": order["id"],
            "clientOrderId": client_order_id,
            "timestamp": 1_750_000_000_000,
            "datetime": "2026-07-06T00:00:00+00:00",
            "side": "buy",
            "amount": 0.5,
            "price": 100.0,
            "fee": {"cost": 0.1, "currency": "USD"},
        })


def _consumer_adapter(venue_state: _Venue, *, kill_in_submit: bool = False):
    class Adapter:
        def __init__(self, venue, sandbox=False):
            pass

        def find_order_by_client_oid(self, symbol, client_order_id):
            if not venue_state.lookup_enabled:
                return None
            return venue_state.orders.get(client_order_id)

        def submit_order(self, **kwargs):
            coid = kwargs["client_order_id"]
            if kill_in_submit:
                # the order reaches the venue, then the process dies before
                # the response is processed
                venue_state.place(coid)
                venue_state.submits.append(dict(kwargs))
                raise _Kill("kill:in_submit_after_placement")
            venue_state.submits.append(dict(kwargs))
            return dict(venue_state.place(coid))

        def close(self):
            pass

    return Adapter


def _wire_consumer(monkeypatch, consumer, venue_state: _Venue, *, kill_in_submit: bool = False):
    _wire_consumer_guards_only(monkeypatch, consumer)
    monkeypatch.setattr(
        consumer, "LiveExchangeAdapter", _consumer_adapter(venue_state, kill_in_submit=kill_in_submit)
    )


def _wire_consumer_guards_only(monkeypatch, consumer):
    """Consumer wiring without replacing LiveExchangeAdapter (caller sets it)."""
    monkeypatch.setenv(consumer.SUBMITTING_STALE_RECOVERY_MS_ENV, "1")
    monkeypatch.setattr(consumer, "live_enabled_and_armed", lambda: (True, "armed"))
    monkeypatch.setattr(consumer, "is_snapshot_fresh", lambda: (True, None))
    monkeypatch.setattr(consumer, "_live_sandbox_enabled", lambda: True)
    monkeypatch.setattr(consumer, "mq_check", lambda venue, symbol: {"ok": True, "last": 100.0})
    monkeypatch.setattr(consumer, "_risk_check_and_claim", lambda db, notional_est: (True, None))

    class Decision:
        allowed = True
        side = "buy"
        order_type = "limit"
        qty = 0.5
        limit_price = 100.0
        reason = "ok"

    async def fake_decide_order(**kwargs):
        return Decision()

    monkeypatch.setattr(consumer, "decide_order", fake_decide_order)

    def fake_sleep(_seconds):
        consumer.STOP_FILE.parent.mkdir(parents=True, exist_ok=True)
        consumer.STOP_FILE.write_text("stop\n")

    monkeypatch.setattr(consumer.time, "sleep", fake_sleep)


def _run_consumer(consumer, *, expect_kill: bool):
    if expect_kill:
        with pytest.raises(SystemExit):
            consumer.run_forever()
        # a real crash leaves the lock behind; stale-lock reclaim is proven in
        # the runner-lock tests, so clear it here to keep this test focused
        if consumer.LOCK_FILE.exists():
            consumer.LOCK_FILE.unlink()
    else:
        consumer.run_forever()


def _reconciler_adapter(venue_state: _Venue):
    class Adapter:
        def __init__(self, venue, sandbox=False):
            pass

        def find_order_by_client_oid(self, symbol, client_order_id):
            if not venue_state.lookup_enabled:
                return None
            return venue_state.orders.get(client_order_id)

        def fetch_order(self, symbol, exchange_order_id):
            for o in venue_state.orders.values():
                if o["id"] == exchange_order_id:
                    return dict(o)
            return None

        def fetch_my_trades(self, symbol, since_ms=None, limit=100):
            since = int(since_ms or 0)
            return [dict(t) for t in venue_state.trades if int(t["timestamp"]) >= since]

        def close(self):
            pass

    return Adapter


def _wire_reconciler(monkeypatch, reconciler, venue_state: _Venue):
    monkeypatch.setattr(reconciler, "_system_guard_reconcile_mode", lambda: ("normal", {}))
    monkeypatch.setattr(reconciler, "live_enabled_and_armed", lambda: (True, "armed"))
    monkeypatch.setattr(reconciler, "_live_sandbox_enabled", lambda: True)
    monkeypatch.setattr(reconciler, "LiveExchangeAdapter", _reconciler_adapter(venue_state))

    def fake_sleep(_seconds):
        reconciler.STOP_FILE.parent.mkdir(parents=True, exist_ok=True)
        reconciler.STOP_FILE.write_text("stop\n")

    monkeypatch.setattr(reconciler.time, "sleep", fake_sleep)


def _run_reconciler(reconciler, *, expect_kill: bool = False):
    if expect_kill:
        with pytest.raises(SystemExit):
            reconciler.run_forever()
        if reconciler.LOCK_FILE.exists():
            reconciler.LOCK_FILE.unlink()
    else:
        reconciler.run_forever()


def _intent_row(queue_mod, intent_id: str) -> dict:
    qdb = queue_mod.LiveIntentQueueSQLite()
    rows = {r["intent_id"]: r for r in qdb.list_intents(limit=20)}
    return rows[intent_id]


def _fill_rows(trading_mod) -> list[dict]:
    import sqlite3

    con = sqlite3.connect(trading_mod.DB_PATH)
    try:
        cur = con.execute("SELECT trade_id, qty, price FROM live_fills")
        return [{"trade_id": r[0], "qty": r[1], "price": r[2]} for r in cur.fetchall()]
    finally:
        con.close()


# ---------------------------------------------------------------------------
# submit path: kill between each side effect, restart, assert exactly-once
# ---------------------------------------------------------------------------


def test_kill_in_submit_then_restart_never_resubmits(monkeypatch, tmp_path):
    """
    Kill inside the venue submit (order placed, response lost). Restart must
    not submit again: the dedupe claim row blocks the main loop, and the
    startup stale-`submitting` recovery sweep verifies the order at the
    venue and converges the intent to `submitted` without resubmitting.
    """
    queue_mod, trading_mod, dedupe_mod, consumer, reconciler = _reload_live_stack(monkeypatch, tmp_path)
    _seed_intent(queue_mod, "s1")
    venue = _Venue()

    _wire_consumer(monkeypatch, consumer, venue, kill_in_submit=True)
    venue.lookup_enabled = False  # phase-1 recovery lookup cannot run: process is dead
    _run_consumer(consumer, expect_kill=True)

    assert len(venue.submits) == 1
    assert _intent_row(queue_mod, "s1")["status"] == "submitting"

    # restart: fresh consumer, venue lookup available again
    venue.lookup_enabled = True
    _wire_consumer(monkeypatch, consumer, venue, kill_in_submit=False)
    _run_consumer(consumer, expect_kill=False)

    assert len(venue.submits) == 1  # the money invariant: exactly one submit
    row = _intent_row(queue_mod, "s1")
    assert row["status"] == "submitted"  # startup sweep converged the stranding
    assert row["exchange_order_id"] == "ex-cid-s1"


def test_kill_after_submit_before_dedupe_mark_then_restart(monkeypatch, tmp_path):
    """
    Venue submit succeeds; process dies inside dedupe.mark_submitted. The
    dedupe row is still `created`, so the restart main loop skips the intent
    without resubmitting, and the startup sweep converges it to `submitted`
    from the venue's record.
    """
    queue_mod, trading_mod, dedupe_mod, consumer, reconciler = _reload_live_stack(monkeypatch, tmp_path)
    _seed_intent(queue_mod, "s2")
    venue = _Venue()

    real_store = dedupe_mod.OrderDedupeStore

    class KillOnMarkSubmitted(real_store):
        def mark_submitted(self, **kwargs):
            raise _Kill("kill:before_dedupe_mark_submitted")

    monkeypatch.setattr(consumer, "OrderDedupeStore", KillOnMarkSubmitted)
    _wire_consumer(monkeypatch, consumer, venue)
    venue.lookup_enabled = False
    _run_consumer(consumer, expect_kill=True)

    assert len(venue.submits) == 1

    monkeypatch.setattr(consumer, "OrderDedupeStore", real_store)
    venue.lookup_enabled = True
    _wire_consumer(monkeypatch, consumer, venue)
    _run_consumer(consumer, expect_kill=False)

    assert len(venue.submits) == 1
    assert _intent_row(queue_mod, "s2")["status"] == "submitted"  # sweep converged


def test_kill_after_dedupe_mark_before_status_write_then_restart(monkeypatch, tmp_path):
    """
    Venue submit + dedupe mark succeed; process dies inside the queue status
    write. The dedupe remote-id guard blocks the restart main loop from
    resubmitting, and the startup sweep converges the row to `submitted`.
    """
    queue_mod, trading_mod, dedupe_mod, consumer, reconciler = _reload_live_stack(monkeypatch, tmp_path)
    _seed_intent(queue_mod, "s3")
    venue = _Venue()

    real_update = consumer.update_live_queue_status_as_intent_consumer

    def kill_on_submitted(qdb, it, status, **kwargs):
        if status == "submitted":
            raise _Kill("kill:before_queue_status_write")
        return real_update(qdb, it, status, **kwargs)

    monkeypatch.setattr(consumer, "update_live_queue_status_as_intent_consumer", kill_on_submitted)
    _wire_consumer(monkeypatch, consumer, venue)
    venue.lookup_enabled = False
    _run_consumer(consumer, expect_kill=True)

    assert len(venue.submits) == 1

    monkeypatch.setattr(consumer, "update_live_queue_status_as_intent_consumer", real_update)
    venue.lookup_enabled = True
    _wire_consumer(monkeypatch, consumer, venue)
    _run_consumer(consumer, expect_kill=False)

    assert len(venue.submits) == 1
    dedupe = dedupe_mod.OrderDedupeStore()
    ded_row = dedupe.claim(exchange_id="coinbase", intent_id="s3", symbol="BTC/USD", client_order_id="cid-s3")
    assert str(ded_row.get("remote_order_id") or "") == "ex-cid-s3"
    assert _intent_row(queue_mod, "s3")["status"] == "submitted"  # sweep converged


def test_kill_after_status_write_reconciler_converges_fill(monkeypatch, tmp_path):
    """
    Crash after the queue says `submitted` but before the order-store upsert.
    Restart + reconciler pass converges: fill accounted exactly once, status
    `filled`; a second pass is a no-op.
    """
    queue_mod, trading_mod, dedupe_mod, consumer, reconciler = _reload_live_stack(monkeypatch, tmp_path)
    _seed_intent(queue_mod, "s4")
    venue = _Venue()

    class KillOnUpsert(trading_mod.LiveTradingSQLite):
        def upsert_order(self, row):
            raise _Kill("kill:before_order_store_upsert")

    monkeypatch.setattr(consumer, "LiveTradingSQLite", KillOnUpsert)
    _wire_consumer(monkeypatch, consumer, venue)
    venue.lookup_enabled = False
    _run_consumer(consumer, expect_kill=True)

    assert len(venue.submits) == 1
    assert _intent_row(queue_mod, "s4")["status"] == "submitted"

    # the venue fills the order before restart
    venue.close_with_trade("cid-s4", trade_id="t-s4-1")

    monkeypatch.setattr(consumer, "LiveTradingSQLite", trading_mod.LiveTradingSQLite)
    _wire_reconciler(monkeypatch, reconciler, venue)
    _run_reconciler(reconciler)

    assert len(venue.submits) == 1
    assert _intent_row(queue_mod, "s4")["status"] == "filled"
    fills = _fill_rows(trading_mod)
    assert [f["trade_id"] for f in fills] == ["t-s4-1"]

    # a second reconciler pass must be a no-op (idempotent convergence)
    _wire_reconciler(monkeypatch, reconciler, venue)
    _run_reconciler(reconciler)
    assert [f["trade_id"] for f in _fill_rows(trading_mod)] == ["t-s4-1"]
    assert _intent_row(queue_mod, "s4")["status"] == "filled"


def test_submit_unknown_converges_via_reconciler_lookup(monkeypatch, tmp_path):
    """
    Submit raises after venue placement and both in-process recovery lookups
    fail (ambiguous-submit lane): phase 1 records `submit_unknown`; the
    reconciler's client-order-id verify lane converges it to `submitted`
    without any second venue submission.
    """
    queue_mod, trading_mod, dedupe_mod, consumer, reconciler = _reload_live_stack(monkeypatch, tmp_path)
    _seed_intent(queue_mod, "s5")
    venue = _Venue()

    class RaiseAfterPlacementAdapter:
        def __init__(self, v, sandbox=False):
            pass

        def find_order_by_client_oid(self, symbol, client_order_id):
            if not venue.lookup_enabled:
                return None
            return venue.orders.get(client_order_id)

        def submit_order(self, **kwargs):
            coid = kwargs["client_order_id"]
            venue.place(coid)
            venue.submits.append(dict(kwargs))
            raise RuntimeError("connection dropped mid-response")

        def close(self):
            pass

    venue.lookup_enabled = False  # both recovery lookups fail in phase 1
    _wire_consumer_guards_only(monkeypatch, consumer)
    monkeypatch.setattr(consumer, "LiveExchangeAdapter", RaiseAfterPlacementAdapter)
    _run_consumer(consumer, expect_kill=False)

    assert len(venue.submits) == 1
    assert _intent_row(queue_mod, "s5")["status"] == "submit_unknown"

    venue.lookup_enabled = True
    _wire_reconciler(monkeypatch, reconciler, venue)
    _run_reconciler(reconciler)

    assert len(venue.submits) == 1
    assert _intent_row(queue_mod, "s5")["status"] == "submitted"


# ---------------------------------------------------------------------------
# fill path: kill between accounting side effects, rerun, assert idempotence
# ---------------------------------------------------------------------------


def _submitted_intent_with_trade(monkeypatch, tmp_path):
    queue_mod, trading_mod, dedupe_mod, consumer, reconciler = _reload_live_stack(monkeypatch, tmp_path)
    _seed_intent(queue_mod, "f1")
    venue = _Venue()
    _wire_consumer(monkeypatch, consumer, venue)
    _run_consumer(consumer, expect_kill=False)
    assert _intent_row(queue_mod, "f1")["status"] == "submitted"
    venue.close_with_trade("cid-f1", trade_id="t-f1-1")
    return queue_mod, trading_mod, consumer, reconciler, venue


def test_kill_in_canonical_fill_accounting_then_rerun_is_idempotent(monkeypatch, tmp_path):
    """
    Kill inside canonical fill accounting after the trading-store fill row is
    written. The cursor must not advance past the unaccounted fill; the rerun
    re-fetches the trade, INSERT OR IGNORE dedupes the trading-store row, the
    accounting succeeds exactly once, and the intent converges to `filled`.
    """
    queue_mod, trading_mod, consumer, reconciler, venue = _submitted_intent_with_trade(monkeypatch, tmp_path)

    real_emit = reconciler._emit_canonical_fill
    emit_calls: list[str] = []

    def kill_first_emit(*, exec_db, fill):
        raise _Kill("kill:in_canonical_fill_accounting")

    monkeypatch.setattr(reconciler, "_emit_canonical_fill", kill_first_emit)
    _wire_reconciler(monkeypatch, reconciler, venue)
    _run_reconciler(reconciler, expect_kill=True)

    # phase 1 left the trading-store fill row but no accounting, no cursor move
    assert [f["trade_id"] for f in _fill_rows(trading_mod)] == ["t-f1-1"]
    assert _intent_row(queue_mod, "f1")["status"] == "submitted"

    def counting_emit(*, exec_db, fill):
        emit_calls.append(str(fill.get("fill_id")))
        return real_emit(exec_db=exec_db, fill=fill)

    monkeypatch.setattr(reconciler, "_emit_canonical_fill", counting_emit)
    _wire_reconciler(monkeypatch, reconciler, venue)
    _run_reconciler(reconciler)

    assert emit_calls == ["t-f1-1"]  # accounted exactly once on rerun
    assert [f["trade_id"] for f in _fill_rows(trading_mod)] == ["t-f1-1"]  # no dup row
    assert _intent_row(queue_mod, "f1")["status"] == "filled"


def _canonical_fill_count(reconciler, fill_id: str) -> int:
    import sqlite3

    exec_db = reconciler._default_exec_db_path()
    con = sqlite3.connect(exec_db)
    try:
        cur = con.execute("SELECT COUNT(*) FROM canonical_fills WHERE fill_id = ?", (fill_id,))
        return int(cur.fetchone()[0])
    finally:
        con.close()


def test_kill_after_accounting_before_filled_transition_converges_via_overlap(monkeypatch, tmp_path):
    """
    Kill after canonical accounting + cursor advance but before the `filled`
    transition. CONVERGENCE-BY-DESIGN PROOF: the reconciler re-fetches a
    60s cursor overlap window (CBP_RECONCILER_CURSOR_OVERLAP_MS), so the
    rerun re-sees the trade; INSERT OR IGNORE in both the trading store and
    the canonical journal absorbs the replay, canonical accounting stays
    exactly-once per fill_id, and the intent converges to `filled`.

    The multi-fill edge beyond the overlap window is covered separately by
    test_multi_fill_cursor_edge_converges_via_lookback.
    """
    queue_mod, trading_mod, consumer, reconciler, venue = _submitted_intent_with_trade(monkeypatch, tmp_path)

    real_update = reconciler.update_live_queue_status_as_reconciler

    def kill_on_filled(qdb, it, status, **kwargs):
        if status == "filled":
            raise _Kill("kill:before_filled_transition")
        return real_update(qdb, it, status, **kwargs)

    monkeypatch.setattr(reconciler, "update_live_queue_status_as_reconciler", kill_on_filled)
    _wire_reconciler(monkeypatch, reconciler, venue)
    _run_reconciler(reconciler, expect_kill=True)

    # phase 1: fill row written, canonical accounting applied, cursor
    # advanced, but the queue still says submitted
    assert [f["trade_id"] for f in _fill_rows(trading_mod)] == ["t-f1-1"]
    assert _canonical_fill_count(reconciler, "t-f1-1") == 1
    assert _intent_row(queue_mod, "f1")["status"] == "submitted"

    monkeypatch.setattr(reconciler, "update_live_queue_status_as_reconciler", real_update)
    emit_calls: list[str] = []
    real_emit = reconciler._emit_canonical_fill

    def counting_emit(*, exec_db, fill):
        emit_calls.append(str(fill.get("fill_id")))
        return real_emit(exec_db=exec_db, fill=fill)

    monkeypatch.setattr(reconciler, "_emit_canonical_fill", counting_emit)
    _wire_reconciler(monkeypatch, reconciler, venue)
    _run_reconciler(reconciler)

    # the overlap window re-fetches the trade (replay by design)...
    assert emit_calls == ["t-f1-1"]
    # ...but every store is idempotent, so accounting stays exactly-once...
    assert [f["trade_id"] for f in _fill_rows(trading_mod)] == ["t-f1-1"]
    assert _canonical_fill_count(reconciler, "t-f1-1") == 1
    # ...and the interrupted transition converges
    assert _intent_row(queue_mod, "f1")["status"] == "filled"


# ---------------------------------------------------------------------------
# multi-fill cursor edge beyond the overlap window (finding (b) closure)
# ---------------------------------------------------------------------------


def test_multi_fill_cursor_edge_converges_via_lookback(monkeypatch, tmp_path):
    """
    Finding (b) closure: intent A's fill is accounted but its `filled`
    transition is killed; a later intent B fills far beyond the 60s overlap
    window and advances the shared venue:symbol cursor past A's fill on the
    rerun (list_intents is newest-first, so B processes before A). A's
    re-fetch then misses its own fill entirely — previously deferring
    forever — and now converges to `filled` via the canonical-journal
    accounted-fill lookback, with accounting still exactly-once.
    """
    queue_mod, trading_mod, dedupe_mod, consumer, reconciler = _reload_live_stack(monkeypatch, tmp_path)
    _seed_intent(queue_mod, "A")
    venue = _Venue()
    _wire_consumer(monkeypatch, consumer, venue)
    _run_consumer(consumer, expect_kill=False)
    assert _intent_row(queue_mod, "A")["status"] == "submitted"

    t1 = 1_750_000_000_000
    venue.orders["cid-A"]["status"] = "closed"
    venue.trades.append({
        "id": "t-A-1", "order": venue.orders["cid-A"]["id"], "clientOrderId": "cid-A",
        "timestamp": t1, "datetime": "2026-07-06T00:00:00+00:00",
        "side": "buy", "amount": 0.5, "price": 100.0, "fee": {"cost": 0.1, "currency": "USD"},
    })

    # pass 1: A's fill accounted + cursor advanced, filled transition killed
    real_update = reconciler.update_live_queue_status_as_reconciler

    def kill_on_filled(qdb, it, status, **kwargs):
        if status == "filled":
            raise _Kill("kill:before_filled_transition")
        return real_update(qdb, it, status, **kwargs)

    monkeypatch.setattr(reconciler, "update_live_queue_status_as_reconciler", kill_on_filled)
    _wire_reconciler(monkeypatch, reconciler, venue)
    _run_reconciler(reconciler, expect_kill=True)
    assert _canonical_fill_count(reconciler, "t-A-1") == 1
    assert _intent_row(queue_mod, "A")["status"] == "submitted"

    # intent B fills 10 minutes later — far beyond the 60s overlap window
    _seed_intent(queue_mod, "B")
    _wire_consumer(monkeypatch, consumer, venue)
    _run_consumer(consumer, expect_kill=False)
    t2 = t1 + 600_000
    venue.orders["cid-B"]["status"] = "closed"
    venue.trades.append({
        "id": "t-B-1", "order": venue.orders["cid-B"]["id"], "clientOrderId": "cid-B",
        "timestamp": t2, "datetime": "2026-07-06T00:10:00+00:00",
        "side": "buy", "amount": 0.5, "price": 100.0, "fee": {"cost": 0.1, "currency": "USD"},
    })

    monkeypatch.setattr(reconciler, "update_live_queue_status_as_reconciler", real_update)
    _wire_reconciler(monkeypatch, reconciler, venue)
    _run_reconciler(reconciler)

    # B converged normally; A converged via lookback despite its fill being
    # outside the cursor overlap re-fetch window
    assert _intent_row(queue_mod, "B")["status"] == "filled"
    assert _intent_row(queue_mod, "A")["status"] == "filled"
    # exactly-once accounting held for both fills
    assert _canonical_fill_count(reconciler, "t-A-1") == 1
    assert _canonical_fill_count(reconciler, "t-B-1") == 1
    assert sorted(f["trade_id"] for f in _fill_rows(trading_mod)) == ["t-A-1", "t-B-1"]
    # A's fill was NOT re-fetched (cursor honesty): the lookback, not a
    # replay, produced the convergence
    cursor = int(queue_mod.LiveIntentQueueSQLite().get_state("trades_since_ms:coinbase:BTC/USD"))
    assert cursor == t2 + 1


def test_fill_lookback_helper_fail_closed(monkeypatch, tmp_path):
    queue_mod, trading_mod, dedupe_mod, consumer, reconciler = _reload_live_stack(monkeypatch, tmp_path)
    exec_db = reconciler._default_exec_db_path()

    # missing db / empty journal -> 0
    assert reconciler._accounted_fills_for_order(str(tmp_path / "nope.sqlite"), venue="coinbase", client_order_id="c", exchange_order_id="e") == 0
    # no identifiers -> 0 without touching the db
    assert reconciler._accounted_fills_for_order(exec_db, venue="coinbase", client_order_id="", exchange_order_id="") == 0

    from services.journal.fill_sink import CanonicalFillSink

    CanonicalFillSink(exec_db=exec_db).on_fill({
        "venue": "coinbase", "fill_id": "lk-1", "symbol": "BTC/USD", "side": "buy",
        "qty": 0.5, "price": 100.0, "ts": "2026-07-06T00:00:00+00:00", "fee_usd": 0.1,
        "client_order_id": "cid-lk", "order_id": "ex-lk",
    })

    assert reconciler._accounted_fills_for_order(exec_db, venue="coinbase", client_order_id="cid-lk", exchange_order_id="") == 1
    assert reconciler._accounted_fills_for_order(exec_db, venue="coinbase", client_order_id="", exchange_order_id="ex-lk") == 1
    assert reconciler._accounted_fills_for_order(exec_db, venue="coinbase", client_order_id="other", exchange_order_id="other") == 0
    assert reconciler._accounted_fills_for_order(exec_db, venue="kraken", client_order_id="cid-lk", exchange_order_id="ex-lk") == 0
