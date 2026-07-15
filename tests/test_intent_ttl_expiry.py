"""
Substrate backlog #18 proofs: intent TTL for live/shadow consumers.

Aged or age-indeterminate queued intents must be marked `expired` (an
operator-visible terminal status) at the live consumer claim boundary and
must produce zero submissions; fresh intents remain eligible. The reconciler
scan sources exclude `expired`, so `expired` is terminal for the reconciler
by construction.
"""
from __future__ import annotations

import importlib
import time
from datetime import datetime, timedelta, timezone

from services.execution import intent_ttl
from services.execution.intent_lifecycle import (
    LIVE_QUEUE_STATUS_TRANSITIONS,
    LIVE_QUEUE_TERMINAL_STATUSES,
    RECONCILER_LIVE_QUEUE_SOURCES,
    RECONCILER_LIVE_QUEUE_TARGETS,
    live_queue_transition_allowed,
)


def _iso_utc(offset_s: float) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_s)).isoformat()


# ---------------------------------------------------------------------------
# check_intent_age unit proofs (fail-closed matrix)
# ---------------------------------------------------------------------------


def test_fresh_intent_passes(monkeypatch):
    monkeypatch.delenv(intent_ttl.INTENT_MAX_AGE_ENV, raising=False)
    out = intent_ttl.check_intent_age(_iso_utc(-5.0))
    assert out["ok"] is True
    assert out["reason"] == "ok"
    assert out["max_age_s"] == intent_ttl.INTENT_MAX_AGE_S_DEFAULT


def test_aged_intent_expires(monkeypatch):
    monkeypatch.delenv(intent_ttl.INTENT_MAX_AGE_ENV, raising=False)
    out = intent_ttl.check_intent_age(_iso_utc(-(2 * intent_ttl.INTENT_MAX_AGE_S_DEFAULT)))
    assert out["ok"] is False
    assert out["reason"].startswith("intent_ttl:expired:")


def test_missing_created_ts_fails_closed(monkeypatch):
    monkeypatch.delenv(intent_ttl.INTENT_MAX_AGE_ENV, raising=False)
    for missing in (None, "", "   "):
        out = intent_ttl.check_intent_age(missing)
        assert out["ok"] is False
        assert out["reason"] == "intent_ttl:missing_created_ts"


def test_invalid_created_ts_fails_closed(monkeypatch):
    monkeypatch.delenv(intent_ttl.INTENT_MAX_AGE_ENV, raising=False)
    for bad in ("not-a-date", "2026-99-99T00:00:00", float("nan"), float("inf"), -1.0, 0):
        out = intent_ttl.check_intent_age(bad)
        assert out["ok"] is False
        assert out["reason"] == "intent_ttl:invalid_created_ts"


def test_future_created_ts_fails_closed(monkeypatch):
    monkeypatch.delenv(intent_ttl.INTENT_MAX_AGE_ENV, raising=False)
    out = intent_ttl.check_intent_age(_iso_utc(3600.0))
    assert out["ok"] is False
    assert out["reason"] == "intent_ttl:future_created_ts"


def test_naive_and_z_suffix_timestamps_are_utc(monkeypatch):
    monkeypatch.delenv(intent_ttl.INTENT_MAX_AGE_ENV, raising=False)
    naive = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    assert intent_ttl.check_intent_age(naive)["ok"] is True
    zulu = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    assert intent_ttl.check_intent_age(zulu)["ok"] is True


def test_epoch_float_created_ts_supported(monkeypatch):
    monkeypatch.delenv(intent_ttl.INTENT_MAX_AGE_ENV, raising=False)
    assert intent_ttl.check_intent_age(time.time() - 5.0)["ok"] is True
    aged = intent_ttl.check_intent_age(time.time() - (2 * intent_ttl.INTENT_MAX_AGE_S_DEFAULT))
    assert aged["ok"] is False
    assert aged["reason"].startswith("intent_ttl:expired:")


def test_window_env_override_and_invalid_fallback(monkeypatch):
    ts = _iso_utc(-120.0)
    monkeypatch.setenv(intent_ttl.INTENT_MAX_AGE_ENV, "60")
    assert intent_ttl.check_intent_age(ts)["ok"] is False
    monkeypatch.setenv(intent_ttl.INTENT_MAX_AGE_ENV, "600")
    assert intent_ttl.check_intent_age(ts)["ok"] is True
    for bad in ("", "abc", "-5", "0", "nan", "inf", "-inf"):
        monkeypatch.setenv(intent_ttl.INTENT_MAX_AGE_ENV, bad)
        out = intent_ttl.check_intent_age(ts)
        assert out["max_age_s"] == intent_ttl.INTENT_MAX_AGE_S_DEFAULT


def test_non_finite_now_epoch_fails_closed(monkeypatch):
    monkeypatch.delenv(intent_ttl.INTENT_MAX_AGE_ENV, raising=False)
    for bad in (float("nan"), float("inf"), float("-inf")):
        out = intent_ttl.check_intent_age(time.time() - 5.0, now_epoch=bad)
        assert out["ok"] is False
        assert out["reason"] == "intent_ttl:invalid_now"


# ---------------------------------------------------------------------------
# lifecycle vocabulary proofs
# ---------------------------------------------------------------------------


def test_expired_is_terminal_in_lifecycle():
    assert "expired" in LIVE_QUEUE_TERMINAL_STATUSES
    assert LIVE_QUEUE_STATUS_TRANSITIONS["expired"] == set()
    assert live_queue_transition_allowed("queued", "expired") is True
    assert live_queue_transition_allowed("submitting", "expired") is True
    for nxt in ("queued", "submitting", "submitted", "filled", "rejected", "held"):
        assert live_queue_transition_allowed("expired", nxt) is False
    # submitted intents are the reconciler's responsibility, not TTL's
    assert live_queue_transition_allowed("submitted", "expired") is False


def test_reconciler_scan_sets_exclude_expired():
    assert "expired" not in RECONCILER_LIVE_QUEUE_SOURCES
    assert "expired" not in RECONCILER_LIVE_QUEUE_TARGETS


# ---------------------------------------------------------------------------
# store transition proofs (real sqlite in tmp dir)
# ---------------------------------------------------------------------------


def _reload_live_queue(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths
    import storage.live_intent_queue_sqlite as queue_mod

    importlib.reload(app_paths)
    importlib.reload(queue_mod)
    return queue_mod


def _intent_row(**overrides):
    row = {
        "intent_id": "ttl-1",
        "created_ts": datetime.now(timezone.utc).isoformat(),
        "ts": datetime.now(timezone.utc).isoformat(),
        "source": "strategy",
        "strategy_id": "ema_cross",
        "venue": "coinbase",
        "symbol": "BTC/USD",
        "side": "buy",
        "order_type": "market",
        "qty": 0.5,
        "limit_price": None,
        "status": "queued",
        "last_error": None,
        "client_order_id": None,
        "exchange_order_id": None,
        "meta": {},
    }
    row.update(overrides)
    return row


def test_store_allows_queued_and_submitting_to_expired(monkeypatch, tmp_path):
    queue_mod = _reload_live_queue(monkeypatch, tmp_path)
    qdb = queue_mod.LiveIntentQueueSQLite()

    qdb.upsert_intent(_intent_row(intent_id="ttl-q"))
    assert qdb.update_status("ttl-q", "expired", last_error="intent_ttl:expired:999s") is True
    rows = {r["intent_id"]: r for r in qdb.list_intents()}
    assert rows["ttl-q"]["status"] == "expired"

    qdb.upsert_intent(_intent_row(intent_id="ttl-s"))
    claimed = qdb.claim_next_queued(limit=5)
    assert [r["intent_id"] for r in claimed] == ["ttl-s"]
    assert qdb.update_status("ttl-s", "expired", last_error="intent_ttl:expired:999s") is True
    rows = {r["intent_id"]: r for r in qdb.list_intents()}
    assert rows["ttl-s"]["status"] == "expired"


def test_store_treats_expired_as_terminal(monkeypatch, tmp_path):
    queue_mod = _reload_live_queue(monkeypatch, tmp_path)
    qdb = queue_mod.LiveIntentQueueSQLite()
    qdb.upsert_intent(_intent_row(intent_id="ttl-t"))
    assert qdb.update_status("ttl-t", "expired", last_error="intent_ttl:expired:999s") is True
    for nxt in ("queued", "submitting", "submitted", "filled", "rejected", "held"):
        assert qdb.update_status("ttl-t", nxt) is False
    rows = {r["intent_id"]: r for r in qdb.list_intents()}
    assert rows["ttl-t"]["status"] == "expired"


def test_store_never_reclaims_expired(monkeypatch, tmp_path):
    queue_mod = _reload_live_queue(monkeypatch, tmp_path)
    qdb = queue_mod.LiveIntentQueueSQLite()
    qdb.upsert_intent(_intent_row(intent_id="ttl-x"))
    assert qdb.update_status("ttl-x", "expired", last_error="intent_ttl:expired:999s") is True
    assert qdb.claim_next_queued(limit=5) == []
    assert qdb.next_queued(limit=5) == []


# ---------------------------------------------------------------------------
# live consumer integration proofs
# ---------------------------------------------------------------------------


def _run_consumer_once(monkeypatch, tmp_path, intents, *, mq_check=None):
    """
    Drive one claim batch through live_intent_consumer.run_forever using the
    established fake-harness pattern; returns recorded activity.
    """
    from services.execution import live_intent_consumer as lic

    activity = {"status_writes": [], "decide_calls": [], "submit_calls": []}

    class FakeQueue:
        def __init__(self):
            self.claimed = False

        def claim_next_queued(self, limit=10):
            if self.claimed:
                raise SystemExit("queue_exhausted")
            self.claimed = True
            return [dict(it) for it in intents]

        def update_status(self, intent_id, status, **kwargs):
            activity["status_writes"].append((intent_id, status, kwargs.get("last_error")))
            return True

        def get_state(self, key):
            return "2026-01-01"

        def reset_risk_state_for_day(self, day):
            return None

        def atomic_risk_claim(self, **kwargs):
            return True, None

    class FakeTrading:
        def upsert_order(self, row):
            return None

    class FakeAdapter:
        def __init__(self, venue, sandbox=False):
            pass

        def find_order_by_client_oid(self, symbol, client_order_id):
            return None

        def submit_order(self, **kwargs):
            activity["submit_calls"].append(dict(kwargs))
            return {"id": "remote-1", "status": "open"}

        def close(self):
            return None

    class FakeDecision:
        allowed = True
        side = "buy"
        order_type = "limit"
        qty = 1.0
        limit_price = 100.0
        reason = "ok"

    async def fake_decide_order(**kwargs):
        activity["decide_calls"].append(dict(kwargs))
        return FakeDecision()

    class FakeDedupe:
        def claim(self, **kwargs):
            return {"status": "created", "remote_order_id": None, "_inserted": True}

        def mark_submitted(self, **kwargs):
            return None

        def mark_unknown(self, **kwargs):
            return None

    monkeypatch.setattr(lic, "STOP_FILE", tmp_path / "live_intent_consumer.stop")
    monkeypatch.setattr(lic, "FLAGS", tmp_path)
    monkeypatch.setattr(lic, "LOCKS", tmp_path)
    monkeypatch.setattr(lic, "STATUS_FILE", tmp_path / "live_intent_consumer.status.json")
    monkeypatch.setattr(lic, "LOCK_FILE", tmp_path / "live_intent_consumer.lock")
    monkeypatch.setattr(lic, "ensure_dirs", lambda: None)
    monkeypatch.setattr(lic, "_acquire_lock", lambda: True)
    monkeypatch.setattr(lic, "_release_lock", lambda: None)
    monkeypatch.setattr(lic, "_write_status", lambda obj: activity["status_writes"].append(("__status__", obj.get("note") or obj.get("status"), obj.get("reason"))))
    monkeypatch.setattr(lic, "live_enabled_and_armed", lambda: (True, "armed"))
    monkeypatch.setattr(lic, "is_snapshot_fresh", lambda: (True, "fresh"))
    monkeypatch.setattr(lic, "_live_sandbox_enabled", lambda: True)
    monkeypatch.setattr(
        lic,
        "mq_check",
        mq_check or (lambda venue, symbol: {"ok": True, "last": 100.0}),
    )
    monkeypatch.setattr(lic, "decide_order", fake_decide_order)
    monkeypatch.setattr(lic, "LiveIntentQueueSQLite", lambda: FakeQueue())
    monkeypatch.setattr(lic, "LiveTradingSQLite", lambda: FakeTrading())
    monkeypatch.setattr(lic, "LiveExchangeAdapter", FakeAdapter)
    monkeypatch.setattr(lic, "OrderDedupeStore", lambda: FakeDedupe())

    try:
        lic.run_forever()
    except SystemExit as exc:
        assert str(exc) == "queue_exhausted"
    return activity


def _fake_intent(intent_id, created_ts):
    return {
        "intent_id": intent_id,
        "created_ts": created_ts,
        "venue": "coinbase",
        "symbol": "BTC/USD",
        "side": "buy",
        "order_type": "limit",
        "qty": 1.0,
        "limit_price": 100.0,
        "client_order_id": f"cid-{intent_id}",
        "status": "queued",
        "meta": {},
    }


def test_consumer_expires_aged_intent_with_zero_submits(monkeypatch, tmp_path):
    monkeypatch.delenv(intent_ttl.INTENT_MAX_AGE_ENV, raising=False)
    aged_ts = _iso_utc(-(4 * intent_ttl.INTENT_MAX_AGE_S_DEFAULT))
    activity = _run_consumer_once(monkeypatch, tmp_path, [_fake_intent("aged-1", aged_ts)])

    expiries = [w for w in activity["status_writes"] if w[0] == "aged-1" and w[1] == "expired"]
    assert len(expiries) == 1
    assert str(expiries[0][2]).startswith("intent_ttl:expired:")
    assert activity["decide_calls"] == []
    assert activity["submit_calls"] == []


def test_consumer_expires_missing_created_ts_with_zero_submits(monkeypatch, tmp_path):
    monkeypatch.delenv(intent_ttl.INTENT_MAX_AGE_ENV, raising=False)
    intent = _fake_intent("no-ts-1", None)
    del intent["created_ts"]
    activity = _run_consumer_once(monkeypatch, tmp_path, [intent])

    expiries = [w for w in activity["status_writes"] if w[0] == "no-ts-1" and w[1] == "expired"]
    assert len(expiries) == 1
    assert expiries[0][2] == "intent_ttl:missing_created_ts"
    assert activity["decide_calls"] == []
    assert activity["submit_calls"] == []


def test_consumer_market_quality_guard_error_rejects_without_submit(monkeypatch, tmp_path):
    monkeypatch.delenv(intent_ttl.INTENT_MAX_AGE_ENV, raising=False)

    def mq_raises(_venue, _symbol):
        raise RuntimeError("mq boom")

    activity = _run_consumer_once(
        monkeypatch,
        tmp_path,
        [_fake_intent("mq-error-1", _iso_utc(-2.0))],
        mq_check=mq_raises,
    )

    rejections = [
        w for w in activity["status_writes"]
        if w[0] == "mq-error-1" and w[1] == "rejected"
    ]
    assert rejections == [("mq-error-1", "rejected", "mq_blocked:guard_error:RuntimeError")]
    assert activity["decide_calls"] == []
    assert activity["submit_calls"] == []


def test_consumer_submits_fresh_intent(monkeypatch, tmp_path):
    monkeypatch.delenv(intent_ttl.INTENT_MAX_AGE_ENV, raising=False)
    activity = _run_consumer_once(monkeypatch, tmp_path, [_fake_intent("fresh-1", _iso_utc(-2.0))])

    assert [w for w in activity["status_writes"] if w[1] == "expired"] == []
    assert len(activity["decide_calls"]) == 1
    assert len(activity["submit_calls"]) == 1


def test_consumer_mixed_batch_expires_only_aged(monkeypatch, tmp_path):
    monkeypatch.delenv(intent_ttl.INTENT_MAX_AGE_ENV, raising=False)
    aged_ts = _iso_utc(-(4 * intent_ttl.INTENT_MAX_AGE_S_DEFAULT))
    activity = _run_consumer_once(
        monkeypatch,
        tmp_path,
        [_fake_intent("aged-2", aged_ts), _fake_intent("fresh-2", _iso_utc(-2.0))],
    )

    expired_ids = [w[0] for w in activity["status_writes"] if w[1] == "expired"]
    assert expired_ids == ["aged-2"]
    assert len(activity["submit_calls"]) == 1
