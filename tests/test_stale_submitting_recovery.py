"""
Substrate backlog #4 finding (a) closure: startup recovery for intents
stranded at `submitting` by a crash between the dedupe claim/venue submit
and the queue status write.

Contract pinned here: the sweep NEVER submits; venue-found rows converge to
`submitted`, venue-absent rows move to `submit_unknown` (the reconciler's
single ambiguity lane), lookup errors and young rows are left untouched,
and missing/unparseable timestamps are treated as aged (safe: the sweep is
read-then-classify).
"""
from __future__ import annotations

import importlib
from datetime import datetime, timedelta, timezone


def _reload(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths
    import storage.live_intent_queue_sqlite as queue_mod
    import storage.live_trading_sqlite as trading_mod
    import storage.order_dedupe_store_sqlite as dedupe_mod
    import services.execution.live_intent_consumer as consumer

    importlib.reload(app_paths)
    importlib.reload(queue_mod)
    importlib.reload(trading_mod)
    importlib.reload(dedupe_mod)
    importlib.reload(consumer)
    return queue_mod, trading_mod, dedupe_mod, consumer


def _seed_submitting(queue_mod, intent_id: str, *, age_s: float | None = 600.0, drop_ts: bool = False):
    qdb = queue_mod.LiveIntentQueueSQLite()
    ts = (
        "not-a-timestamp"  # store coerces empty created_ts to now; corruption is
        # the only real-world shape of a missing/unusable timestamp
        if drop_ts
        else (datetime.now(timezone.utc) - timedelta(seconds=float(age_s or 0.0))).isoformat()
    )
    qdb.upsert_intent({
        "intent_id": intent_id,
        "created_ts": ts,
        "ts": ts,
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
    claimed = qdb.claim_next_queued(limit=5)
    assert [r["intent_id"] for r in claimed] == [intent_id]
    # claim_next_queued stamps updated_ts=now; a crash-stranded row carries the
    # OLD claim time, so age it directly to mirror the real stranding shape
    import sqlite3

    con = sqlite3.connect(queue_mod.DB_PATH)
    try:
        con.execute(
            "UPDATE live_trade_intents SET updated_ts = ?, created_ts = ? WHERE intent_id = ?",
            (ts, ts, intent_id),
        )
        con.commit()
    finally:
        con.close()
    return qdb


class _Adapter:
    def __init__(self, orders: dict, *, raise_lookup: bool = False):
        self.orders = orders
        self.raise_lookup = raise_lookup
        self.lookups = 0
        self.submits = 0

    def __call__(self, venue, sandbox=False):
        return self

    def find_order_by_client_oid(self, symbol, client_order_id):
        self.lookups += 1
        if self.raise_lookup:
            raise RuntimeError("venue unreachable")
        return self.orders.get(client_order_id)

    def submit_order(self, **kwargs):
        self.submits += 1
        raise AssertionError("recovery sweep must never submit")

    def close(self):
        pass


def _run_sweep(monkeypatch, consumer, queue_mod, trading_mod, dedupe_mod, adapter):
    monkeypatch.setattr(consumer, "_live_sandbox_enabled", lambda: True)
    monkeypatch.setattr(consumer, "LiveExchangeAdapter", adapter)
    qdb = queue_mod.LiveIntentQueueSQLite()
    ldb = trading_mod.LiveTradingSQLite()
    dedupe = dedupe_mod.OrderDedupeStore()
    return consumer._recover_stale_submitting(qdb, ldb, dedupe), qdb, dedupe


def _status(queue_mod, intent_id):
    qdb = queue_mod.LiveIntentQueueSQLite()
    return {r["intent_id"]: r for r in qdb.list_intents(limit=20)}[intent_id]


def test_aged_row_with_venue_order_converges_to_submitted(monkeypatch, tmp_path):
    queue_mod, trading_mod, dedupe_mod, consumer = _reload(monkeypatch, tmp_path)
    _seed_submitting(queue_mod, "a1", age_s=600.0)
    adapter = _Adapter({"cid-a1": {"id": "ex-a1", "clientOrderId": "cid-a1", "status": "open"}})

    out, qdb, dedupe = _run_sweep(monkeypatch, consumer, queue_mod, trading_mod, dedupe_mod, adapter)

    assert out["recovered_submitted"] == 1
    assert adapter.submits == 0
    row = _status(queue_mod, "a1")
    assert row["status"] == "submitted"
    assert row["exchange_order_id"] == "ex-a1"
    ded = dedupe.claim(exchange_id="coinbase", intent_id="a1", symbol="BTC/USD", client_order_id="cid-a1")
    assert str(ded.get("remote_order_id") or "") == "ex-a1"


def test_aged_row_without_venue_order_moves_to_submit_unknown(monkeypatch, tmp_path):
    queue_mod, trading_mod, dedupe_mod, consumer = _reload(monkeypatch, tmp_path)
    _seed_submitting(queue_mod, "a2", age_s=600.0)
    adapter = _Adapter({})

    out, qdb, dedupe = _run_sweep(monkeypatch, consumer, queue_mod, trading_mod, dedupe_mod, adapter)

    assert out["moved_submit_unknown"] == 1
    assert adapter.submits == 0
    row = _status(queue_mod, "a2")
    assert row["status"] == "submit_unknown"
    assert row["last_error"] == "stale_submitting_recovery:order_not_found"


def test_young_row_is_left_untouched(monkeypatch, tmp_path):
    queue_mod, trading_mod, dedupe_mod, consumer = _reload(monkeypatch, tmp_path)
    _seed_submitting(queue_mod, "a3", age_s=1.0)  # default threshold is 120s
    adapter = _Adapter({"cid-a3": {"id": "ex-a3"}})

    out, qdb, dedupe = _run_sweep(monkeypatch, consumer, queue_mod, trading_mod, dedupe_mod, adapter)

    assert out["left_untouched"] == 1
    assert adapter.lookups == 0  # no venue call for young rows
    assert _status(queue_mod, "a3")["status"] == "submitting"


def test_lookup_error_leaves_row_untouched(monkeypatch, tmp_path):
    queue_mod, trading_mod, dedupe_mod, consumer = _reload(monkeypatch, tmp_path)
    _seed_submitting(queue_mod, "a4", age_s=600.0)
    adapter = _Adapter({}, raise_lookup=True)

    out, qdb, dedupe = _run_sweep(monkeypatch, consumer, queue_mod, trading_mod, dedupe_mod, adapter)

    assert out["left_untouched"] == 1
    assert _status(queue_mod, "a4")["status"] == "submitting"


def test_unparseable_timestamps_are_treated_as_aged(monkeypatch, tmp_path):
    queue_mod, trading_mod, dedupe_mod, consumer = _reload(monkeypatch, tmp_path)
    _seed_submitting(queue_mod, "a5", drop_ts=True)  # corrupted ts columns
    adapter = _Adapter({"cid-a5": {"id": "ex-a5"}})

    out, qdb, dedupe = _run_sweep(monkeypatch, consumer, queue_mod, trading_mod, dedupe_mod, adapter)

    assert out["recovered_submitted"] == 1
    assert _status(queue_mod, "a5")["status"] == "submitted"


def test_threshold_env_override_and_invalid_fallback(monkeypatch, tmp_path):
    queue_mod, trading_mod, dedupe_mod, consumer = _reload(monkeypatch, tmp_path)

    monkeypatch.setenv(consumer.SUBMITTING_STALE_RECOVERY_MS_ENV, "60000")
    assert consumer._submitting_stale_recovery_ms() == 60000.0
    for bad in ("", "abc", "-5", "0", "nan", "inf", "-inf"):
        monkeypatch.setenv(consumer.SUBMITTING_STALE_RECOVERY_MS_ENV, bad)
        assert consumer._submitting_stale_recovery_ms() == consumer.SUBMITTING_STALE_RECOVERY_MS_DEFAULT

    monkeypatch.delenv(consumer.SUBMITTING_STALE_RECOVERY_MS_ENV, raising=False)
    monkeypatch.setenv(consumer.SUBMITTING_STALE_RECOVERY_MS_ENV, "1")
    _seed_submitting(queue_mod, "a6", age_s=2.0)  # aged under 1ms threshold
    adapter = _Adapter({"cid-a6": {"id": "ex-a6"}})
    out, qdb, dedupe = _run_sweep(monkeypatch, consumer, queue_mod, trading_mod, dedupe_mod, adapter)
    assert out["recovered_submitted"] == 1


def test_sweep_never_submits_even_for_many_aged_rows(monkeypatch, tmp_path):
    queue_mod, trading_mod, dedupe_mod, consumer = _reload(monkeypatch, tmp_path)
    for i in range(3):
        _seed_submitting(queue_mod, f"m{i}", age_s=600.0)
    adapter = _Adapter({"cid-m0": {"id": "ex-m0"}})  # one found, two absent

    out, qdb, dedupe = _run_sweep(monkeypatch, consumer, queue_mod, trading_mod, dedupe_mod, adapter)

    assert adapter.submits == 0
    assert out["recovered_submitted"] == 1
    assert out["moved_submit_unknown"] == 2
