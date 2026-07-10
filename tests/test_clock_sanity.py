"""
Clock/venue-time sanity proofs (live blocker: every window-based safety
mechanism assumes sane clocks).

Contract pinned here: skew is measured against the round-trip midpoint;
the gate blocks ONLY on an affirmative measured skew beyond
CBP_MAX_CLOCK_SKEW_MS; unsupported venues are a recorded limitation and
never block; measurement errors never block (deliberate v1 boundary); OK
results are cached for CBP_CLOCK_SKEW_CHECK_INTERVAL_S while exceeded and
failed measurements are never cached; the consumer rejects intents with
`clock_skew_blocked:*` and zero venue submits when the gate fails.
"""
from __future__ import annotations

import importlib
from datetime import datetime, timezone

import pytest

from services.execution import clock_sanity


@pytest.fixture(autouse=True)
def _fresh_cache():
    clock_sanity._reset_cache()
    yield
    clock_sanity._reset_cache()


class _Ex:
    def __init__(self, venue_ms, *, supported=True, raise_exc=None):
        self.has = {"fetchTime": supported}
        self._venue_ms = venue_ms
        self._raise = raise_exc
        self.calls = 0

    def fetch_time(self):
        self.calls += 1
        if self._raise is not None:
            raise self._raise
        return self._venue_ms


# ---------------------------------------------------------------------------
# measurement math
# ---------------------------------------------------------------------------


def test_skew_measured_against_round_trip_midpoint():
    t = iter([1_000_000.0, 1_000_100.0])  # midpoint 1_000_050, rtt 100
    r = clock_sanity.measure_venue_skew(_Ex(1_000_500.0), local_ms=lambda: next(t))
    assert r["measured"] is True
    assert r["skew_ms"] == 450.0
    assert r["rtt_ms"] == 100.0
    assert r["reason"] == "ok"


def test_negative_skew_measured():
    t = iter([1_000_000.0, 1_000_100.0])
    r = clock_sanity.measure_venue_skew(_Ex(999_050.0), local_ms=lambda: next(t))
    assert r["skew_ms"] == -1000.0


def test_unsupported_venue_is_limitation_record():
    r = clock_sanity.measure_venue_skew(_Ex(1.0, supported=False))
    assert r["supported"] is False
    assert r["measured"] is False
    assert r["reason"] == "venue_time_unsupported"


def test_fetch_time_error_is_unmeasured():
    r = clock_sanity.measure_venue_skew(_Ex(0, raise_exc=RuntimeError("down")))
    assert r["supported"] is True
    assert r["measured"] is False
    assert r["reason"] == "measure_error:RuntimeError"


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), 0.0, -5.0, "abc", None])
def test_invalid_venue_time_is_unmeasured(bad):
    t = iter([1_000_000.0, 1_000_100.0])
    r = clock_sanity.measure_venue_skew(_Ex(bad), local_ms=lambda: next(t))
    assert r["measured"] is False
    assert r["reason"] == "invalid_venue_time"


# ---------------------------------------------------------------------------
# gate semantics + caching
# ---------------------------------------------------------------------------


def _factory(ex):
    def make():
        make.calls += 1
        return ex

    make.calls = 0
    return make


def test_gate_blocks_only_on_affirmative_excess(monkeypatch):
    monkeypatch.setenv(clock_sanity.MAX_CLOCK_SKEW_MS_ENV, "100")
    now_ms = 1_750_000_000_000.0
    monkeypatch.setattr(clock_sanity.time, "time", lambda: now_ms / 1000.0)

    ok = clock_sanity.check_venue_clock("v1", _factory(_Ex(now_ms + 50.0)))
    assert ok["ok"] is True and ok["exceeded"] is False

    clock_sanity._reset_cache()
    bad = clock_sanity.check_venue_clock("v1", _factory(_Ex(now_ms + 500.0)))
    assert bad["ok"] is False and bad["exceeded"] is True
    assert bad["reason"].startswith("clock_skew_exceeded:")


def test_unsupported_and_unmeasured_never_block():
    r1 = clock_sanity.check_venue_clock("nofetch", _factory(_Ex(1.0, supported=False)))
    assert r1["ok"] is True and r1["reason"] == "venue_time_unsupported"
    r2 = clock_sanity.check_venue_clock("err", _factory(_Ex(0, raise_exc=RuntimeError("x"))))
    assert r2["ok"] is True and r2["measured"] is False

    def broken_factory():
        raise OSError("no network")

    r3 = clock_sanity.check_venue_clock("brokenf", broken_factory)
    assert r3["ok"] is True and r3["reason"].startswith("factory_error:")


def test_ok_results_cached_for_interval(monkeypatch):
    ex = _Ex(1_750_000_000_000.0)
    monkeypatch.setattr(clock_sanity.time, "time", lambda: 1_750_000_000.0)
    clock = iter([0.0, 10.0, 400.0])
    mono = lambda: 0.0  # noqa: E731
    f = _factory(ex)

    r1 = clock_sanity.check_venue_clock("cv", f, monotonic=lambda: 0.0)
    assert r1["cached"] is False and f.calls == 1
    r2 = clock_sanity.check_venue_clock("cv", f, monotonic=lambda: 10.0)
    assert r2["cached"] is True and f.calls == 1  # within default 300s interval
    r3 = clock_sanity.check_venue_clock("cv", f, monotonic=lambda: 400.0)
    assert r3["cached"] is False and f.calls == 2  # interval elapsed


def test_exceeded_results_are_never_cached(monkeypatch):
    monkeypatch.setenv(clock_sanity.MAX_CLOCK_SKEW_MS_ENV, "100")
    now_ms = 1_750_000_000_000.0
    monkeypatch.setattr(clock_sanity.time, "time", lambda: now_ms / 1000.0)
    f = _factory(_Ex(now_ms + 500.0))

    r1 = clock_sanity.check_venue_clock("hot", f, monotonic=lambda: 0.0)
    r2 = clock_sanity.check_venue_clock("hot", f, monotonic=lambda: 1.0)
    assert r1["ok"] is False and r2["ok"] is False
    assert f.calls == 2  # re-measured immediately: blips clear fast


def test_unsupported_venue_is_cached(monkeypatch):
    f = _factory(_Ex(1.0, supported=False))
    clock_sanity.check_venue_clock("nx", f, monotonic=lambda: 0.0)
    clock_sanity.check_venue_clock("nx", f, monotonic=lambda: 10.0)
    assert f.calls == 1


def test_env_overrides_and_invalid_fallback(monkeypatch):
    monkeypatch.setenv(clock_sanity.MAX_CLOCK_SKEW_MS_ENV, "2500")
    assert clock_sanity.max_clock_skew_ms() == 2500.0
    monkeypatch.setenv(clock_sanity.CLOCK_SKEW_CHECK_INTERVAL_S_ENV, "60")
    assert clock_sanity.clock_skew_check_interval_s() == 60.0
    for bad in ("", "abc", "-5", "0", "nan", "inf", "-inf"):
        monkeypatch.setenv(clock_sanity.MAX_CLOCK_SKEW_MS_ENV, bad)
        assert clock_sanity.max_clock_skew_ms() == clock_sanity.MAX_CLOCK_SKEW_MS_DEFAULT
        monkeypatch.setenv(clock_sanity.CLOCK_SKEW_CHECK_INTERVAL_S_ENV, bad)
        assert clock_sanity.clock_skew_check_interval_s() == clock_sanity.CLOCK_SKEW_CHECK_INTERVAL_S_DEFAULT


# ---------------------------------------------------------------------------
# consumer integration
# ---------------------------------------------------------------------------


def _reload_consumer(monkeypatch, tmp_path):
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
    return queue_mod, consumer


def _seed_intent(queue_mod, intent_id: str):
    qdb = queue_mod.LiveIntentQueueSQLite()
    ts = datetime.now(timezone.utc).isoformat()
    qdb.upsert_intent({
        "intent_id": intent_id, "created_ts": ts, "ts": ts, "source": "strategy",
        "venue": "coinbase", "symbol": "BTC/USD", "side": "buy", "order_type": "limit",
        "qty": 0.5, "limit_price": 100.0, "status": "queued", "last_error": None,
        "client_order_id": f"cid-{intent_id}", "exchange_order_id": None,
    })
    return qdb


def _wire(monkeypatch, consumer, submits: list):
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

    class Adapter:
        def __init__(self, venue, sandbox=False):
            pass

        def find_order_by_client_oid(self, symbol, client_order_id):
            return None

        def submit_order(self, **kwargs):
            submits.append(dict(kwargs))
            return {"id": f"ex-{kwargs['client_order_id']}", "status": "open"}

        def close(self):
            pass

    monkeypatch.setattr(consumer, "LiveExchangeAdapter", Adapter)

    def fake_sleep(_s):
        consumer.STOP_FILE.parent.mkdir(parents=True, exist_ok=True)
        consumer.STOP_FILE.write_text("stop\n")

    monkeypatch.setattr(consumer.time, "sleep", fake_sleep)


def test_consumer_rejects_on_exceeded_skew_with_zero_submits(monkeypatch, tmp_path):
    queue_mod, consumer = _reload_consumer(monkeypatch, tmp_path)
    _seed_intent(queue_mod, "c1")
    submits: list = []
    _wire(monkeypatch, consumer, submits)
    monkeypatch.setattr(consumer, "check_venue_clock", lambda venue, factory: {
        "ok": False, "reason": "clock_skew_exceeded:9000ms", "venue": venue,
        "skew_ms": 9000.0, "rtt_ms": 50.0, "threshold_ms": 5000.0,
    })

    consumer.run_forever()

    assert submits == []
    qdb = queue_mod.LiveIntentQueueSQLite()
    row = {r["intent_id"]: r for r in qdb.list_intents(limit=10)}["c1"]
    assert row["status"] == "rejected"
    assert row["last_error"] == "clock_skew_blocked:clock_skew_exceeded:9000ms"


def test_consumer_submits_when_clock_ok(monkeypatch, tmp_path):
    queue_mod, consumer = _reload_consumer(monkeypatch, tmp_path)
    _seed_intent(queue_mod, "c2")
    submits: list = []
    _wire(monkeypatch, consumer, submits)
    monkeypatch.setattr(consumer, "check_venue_clock", lambda venue, factory: {"ok": True, "reason": "ok"})

    consumer.run_forever()

    assert len(submits) == 1
    qdb = queue_mod.LiveIntentQueueSQLite()
    row = {r["intent_id"]: r for r in qdb.list_intents(limit=10)}["c2"]
    assert row["status"] == "submitted"
