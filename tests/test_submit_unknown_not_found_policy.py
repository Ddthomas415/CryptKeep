"""
Substrate backlog #3 remaining thread: terminal disposition policy for
submit_unknown intents the venue consistently reports as not found.

Contract pinned here: only clean not-found answers count as observations
(lookup exceptions never reach the counter); disposition to `error`
requires BOTH thresholds — at least CBP_SUBMIT_UNKNOWN_NOT_FOUND_MIN_OBS
observations AND CBP_SUBMIT_UNKNOWN_NOT_FOUND_TERMINAL_MS of age since the
first observation; a successful recovery clears the record; corrupt
tracking records restart the window (fail toward NOT disposing).
"""
from __future__ import annotations

import importlib
import json
from datetime import datetime, timezone


def _reload(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths
    import storage.live_intent_queue_sqlite as queue_mod
    import storage.live_trading_sqlite as trading_mod
    import services.execution.live_reconciler as reconciler

    importlib.reload(app_paths)
    importlib.reload(queue_mod)
    importlib.reload(trading_mod)
    importlib.reload(reconciler)
    return queue_mod, trading_mod, reconciler


def _seed_submit_unknown(queue_mod, intent_id: str):
    qdb = queue_mod.LiveIntentQueueSQLite()
    ts = datetime.now(timezone.utc).isoformat()
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
    assert qdb.update_status(intent_id, "submit_unknown", last_error="ambiguous") is True
    return qdb


class _Adapter:
    def __init__(self, order=None):
        self.order = order
        self.lookups = 0

    def find_order_by_client_oid(self, symbol, client_order_id):
        self.lookups += 1
        return self.order

    def close(self):
        pass


def _intent(queue_mod, intent_id):
    qdb = queue_mod.LiveIntentQueueSQLite()
    return {r["intent_id"]: r for r in qdb.list_intents(limit=20)}[intent_id]


def _recover(reconciler, queue_mod, trading_mod, adapter, intent_row):
    qdb = queue_mod.LiveIntentQueueSQLite()
    ldb = trading_mod.LiveTradingSQLite()
    return reconciler._recover_submit_unknown_by_client_order_id(
        qdb=qdb, ldb=ldb, ad=adapter, intent=intent_row, venue="coinbase", symbol="BTC/USD",
    )


def test_not_found_under_thresholds_stays_submit_unknown(monkeypatch, tmp_path):
    queue_mod, trading_mod, reconciler = _reload(monkeypatch, tmp_path)
    _seed_submit_unknown(queue_mod, "n1")
    adapter = _Adapter(order=None)

    for _ in range(2):  # below default min_obs=3
        out = _recover(reconciler, queue_mod, trading_mod, adapter, _intent(queue_mod, "n1"))
        assert out is False

    row = _intent(queue_mod, "n1")
    assert row["status"] == "submit_unknown"
    qdb = queue_mod.LiveIntentQueueSQLite()
    state = json.loads(qdb.get_state(reconciler._su_not_found_state_key("n1")))
    assert state["count"] == 2


def test_obs_threshold_alone_does_not_dispose(monkeypatch, tmp_path):
    """Many observations inside a short window must not dispose (age gate)."""
    queue_mod, trading_mod, reconciler = _reload(monkeypatch, tmp_path)
    _seed_submit_unknown(queue_mod, "n2")
    adapter = _Adapter(order=None)

    for _ in range(10):  # >> min_obs, but age << 15 min default
        _recover(reconciler, queue_mod, trading_mod, adapter, _intent(queue_mod, "n2"))

    assert _intent(queue_mod, "n2")["status"] == "submit_unknown"


def test_both_thresholds_dispose_to_error(monkeypatch, tmp_path):
    queue_mod, trading_mod, reconciler = _reload(monkeypatch, tmp_path)
    _seed_submit_unknown(queue_mod, "n3")
    adapter = _Adapter(order=None)
    qdb = queue_mod.LiveIntentQueueSQLite()

    for _ in range(2):
        _recover(reconciler, queue_mod, trading_mod, adapter, _intent(queue_mod, "n3"))
    # backdate the first observation beyond the 15-minute default window
    key = reconciler._su_not_found_state_key("n3")
    state = json.loads(qdb.get_state(key))
    state["first_ms"] = int(state["first_ms"]) - 20 * 60 * 1000
    qdb.set_state(key, json.dumps(state))

    out = _recover(reconciler, queue_mod, trading_mod, adapter, _intent(queue_mod, "n3"))

    assert out is True
    row = _intent(queue_mod, "n3")
    assert row["status"] == "error"
    assert str(row["last_error"]).startswith("submit_unknown_not_found_terminal:obs=3:")
    # tracking record cleared after disposition
    assert not (qdb.get_state(key) or "")
    # order store carries the audit row
    import sqlite3

    con = sqlite3.connect(trading_mod.DB_PATH)
    try:
        r = con.execute(
            "SELECT status, last_error FROM live_orders WHERE client_order_id = ?", ("cid-n3",)
        ).fetchone()
    finally:
        con.close()
    assert r[0] == "error"
    assert str(r[1]).startswith("submit_unknown_not_found_terminal:")


def test_recovery_clears_observation_record(monkeypatch, tmp_path):
    queue_mod, trading_mod, reconciler = _reload(monkeypatch, tmp_path)
    _seed_submit_unknown(queue_mod, "n4")
    qdb = queue_mod.LiveIntentQueueSQLite()

    _recover(reconciler, queue_mod, trading_mod, _Adapter(order=None), _intent(queue_mod, "n4"))
    assert json.loads(qdb.get_state(reconciler._su_not_found_state_key("n4")))["count"] == 1

    found = _Adapter(order={"id": "ex-n4", "clientOrderId": "cid-n4"})
    out = _recover(reconciler, queue_mod, trading_mod, found, _intent(queue_mod, "n4"))

    assert out is True
    assert _intent(queue_mod, "n4")["status"] == "submitted"
    assert not (qdb.get_state(reconciler._su_not_found_state_key("n4")) or "")


def test_corrupt_tracking_record_restarts_window(monkeypatch, tmp_path):
    """Fail toward NOT disposing: garbage state restarts the observation window."""
    queue_mod, trading_mod, reconciler = _reload(monkeypatch, tmp_path)
    _seed_submit_unknown(queue_mod, "n5")
    qdb = queue_mod.LiveIntentQueueSQLite()
    qdb.set_state(reconciler._su_not_found_state_key("n5"), "{not json")

    out = _recover(reconciler, queue_mod, trading_mod, _Adapter(order=None), _intent(queue_mod, "n5"))

    assert out is False
    assert _intent(queue_mod, "n5")["status"] == "submit_unknown"
    state = json.loads(qdb.get_state(reconciler._su_not_found_state_key("n5")))
    assert state["count"] == 1  # window restarted, not disposed


def test_env_overrides_and_invalid_fallback(monkeypatch, tmp_path):
    queue_mod, trading_mod, reconciler = _reload(monkeypatch, tmp_path)

    monkeypatch.setenv(reconciler.SU_NOT_FOUND_TERMINAL_MS_ENV, "60000")
    assert reconciler._su_not_found_terminal_ms() == 60000.0
    monkeypatch.setenv(reconciler.SU_NOT_FOUND_MIN_OBS_ENV, "5")
    assert reconciler._su_not_found_min_obs() == 5
    for bad in ("", "abc", "-5", "0", "nan", "inf", "-inf"):
        monkeypatch.setenv(reconciler.SU_NOT_FOUND_TERMINAL_MS_ENV, bad)
        assert reconciler._su_not_found_terminal_ms() == reconciler.SU_NOT_FOUND_TERMINAL_MS_DEFAULT
        monkeypatch.setenv(reconciler.SU_NOT_FOUND_MIN_OBS_ENV, bad)
        assert reconciler._su_not_found_min_obs() == reconciler.SU_NOT_FOUND_MIN_OBS_DEFAULT

    # tightened thresholds actually dispose end to end
    monkeypatch.setenv(reconciler.SU_NOT_FOUND_TERMINAL_MS_ENV, "1")
    monkeypatch.setenv(reconciler.SU_NOT_FOUND_MIN_OBS_ENV, "1")
    _seed_submit_unknown(queue_mod, "n6")
    import time

    _recover(reconciler, queue_mod, trading_mod, _Adapter(order=None), _intent(queue_mod, "n6"))
    time.sleep(0.005)
    out = _recover(reconciler, queue_mod, trading_mod, _Adapter(order=None), _intent(queue_mod, "n6"))
    assert out is True
    assert _intent(queue_mod, "n6")["status"] == "error"
