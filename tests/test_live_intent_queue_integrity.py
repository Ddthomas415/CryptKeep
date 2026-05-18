from __future__ import annotations

import importlib

from services.execution.intent_lifecycle import live_queue_transition_allowed


def _reload_queue(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths
    import storage.live_intent_queue_sqlite as queue_mod

    importlib.reload(app_paths)
    importlib.reload(queue_mod)
    return queue_mod


def test_live_intent_queue_upsert_preserves_creation_and_link_fields(monkeypatch, tmp_path):
    queue_mod = _reload_queue(monkeypatch, tmp_path)
    qdb = queue_mod.LiveIntentQueueSQLite()

    qdb.upsert_intent(
        {
            "intent_id": "intent-1",
            "created_ts": "2026-04-02T12:00:00Z",
            "ts": "2026-04-02T12:00:00Z",
            "source": "strategy",
            "venue": "coinbase",
            "symbol": "BTC/USD",
            "side": "buy",
            "order_type": "market",
            "qty": 0.5,
            "limit_price": None,
            "status": "queued",
            "last_error": None,
            "client_order_id": "cid-1",
            "exchange_order_id": "ord-1",
        }
    )

    qdb.upsert_intent(
        {
            "intent_id": "intent-1",
            "created_ts": "2099-01-01T00:00:00Z",
            "ts": "2026-04-02T12:05:00Z",
            "source": "strategy_refresh",
            "venue": "coinbase",
            "symbol": "BTC/USD",
            "side": "sell",
            "order_type": "limit",
            "qty": 1.25,
            "limit_price": 101.5,
            "status": "queued",
            "last_error": "should_not_replace",
            "client_order_id": None,
            "exchange_order_id": None,
        }
    )

    row = qdb.list_intents(limit=5)[0]
    assert row["intent_id"] == "intent-1"
    assert row["created_ts"] == "2026-04-02T12:00:00Z"
    assert row["client_order_id"] == "cid-1"
    assert row["exchange_order_id"] == "ord-1"
    assert row["last_error"] is None
    assert row["ts"] == "2026-04-02T12:05:00Z"
    assert row["source"] == "strategy_refresh"
    assert row["side"] == "sell"
    assert row["order_type"] == "limit"
    assert row["qty"] == 1.25
    assert row["limit_price"] == 101.5


def test_live_intent_queue_update_status_still_updates_mutable_fields(monkeypatch, tmp_path):
    queue_mod = _reload_queue(monkeypatch, tmp_path)
    qdb = queue_mod.LiveIntentQueueSQLite()

    qdb.upsert_intent(
        {
            "intent_id": "intent-2",
            "created_ts": "2026-04-02T12:00:00Z",
            "ts": "2026-04-02T12:00:00Z",
            "source": "strategy",
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
        }
    )

    qdb.update_status(
        "intent-2",
        "submitted",
        last_error=None,
        client_order_id="cid-2",
        exchange_order_id="ord-2",
    )

    row = qdb.list_intents(limit=5)[0]
    assert row["intent_id"] == "intent-2"
    assert row["status"] == "submitted"
    assert row["client_order_id"] == "cid-2"
    assert row["exchange_order_id"] == "ord-2"


def test_live_intent_queue_transition_rules_are_shared_lifecycle_truth() -> None:
    assert live_queue_transition_allowed("queued", "submitted") is True
    assert live_queue_transition_allowed("submitted", "filled") is True
    assert live_queue_transition_allowed("submitted", "queued") is False
    assert live_queue_transition_allowed("filled", "error") is False


def test_live_intent_queue_update_status_blocks_invalid_transition(monkeypatch, tmp_path):
    queue_mod = _reload_queue(monkeypatch, tmp_path)
    qdb = queue_mod.LiveIntentQueueSQLite()

    qdb.upsert_intent(
        {
            "intent_id": "intent-3",
            "created_ts": "2026-04-02T12:00:00Z",
            "ts": "2026-04-02T12:00:00Z",
            "source": "strategy",
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
        }
    )
    qdb.update_status("intent-3", "submitted", client_order_id="cid-3", exchange_order_id="ord-3")

    qdb.update_status(
        "intent-3",
        "queued",
        last_error="should_not_apply",
        client_order_id="bad-cid",
        exchange_order_id="bad-ord",
    )

    row = qdb.list_intents(limit=5)[0]
    assert row["status"] == "submitted"
    assert row["last_error"] is None
    assert row["client_order_id"] == "cid-3"
    assert row["exchange_order_id"] == "ord-3"


def test_live_intent_queue_update_status_blocks_terminal_overwrite(monkeypatch, tmp_path):
    queue_mod = _reload_queue(monkeypatch, tmp_path)
    qdb = queue_mod.LiveIntentQueueSQLite()

    qdb.upsert_intent(
        {
            "intent_id": "intent-4",
            "created_ts": "2026-04-02T12:00:00Z",
            "ts": "2026-04-02T12:00:00Z",
            "source": "strategy",
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
        }
    )
    qdb.update_status("intent-4", "submitted", client_order_id="cid-4", exchange_order_id="ord-4")
    qdb.update_status("intent-4", "filled", last_error=None)

    qdb.update_status("intent-4", "error", last_error="late_error")

    row = qdb.list_intents(limit=5)[0]
    assert row["status"] == "filled"
    assert row["last_error"] is None


def test_live_intent_queue_upsert_does_not_override_terminal_state(monkeypatch, tmp_path):
    queue_mod = _reload_queue(monkeypatch, tmp_path)
    qdb = queue_mod.LiveIntentQueueSQLite()

    qdb.upsert_intent(
        {
            "intent_id": "intent-upsert-terminal",
            "created_ts": "2026-04-02T12:00:00Z",
            "ts": "2026-04-02T12:00:00Z",
            "source": "strategy",
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
        }
    )
    assert qdb.update_status("intent-upsert-terminal", "submitted", client_order_id="cid-5", exchange_order_id="ord-5") is True
    assert qdb.update_status("intent-upsert-terminal", "filled", last_error=None) is True

    qdb.upsert_intent(
        {
            "intent_id": "intent-upsert-terminal",
            "created_ts": "2099-01-01T00:00:00Z",
            "ts": "2026-04-02T12:05:00Z",
            "source": "stale_writer",
            "venue": "coinbase",
            "symbol": "BTC/USD",
            "side": "sell",
            "order_type": "limit",
            "qty": 1.25,
            "limit_price": 101.5,
            "status": "queued",
            "last_error": "should_not_apply",
            "client_order_id": None,
            "exchange_order_id": None,
        }
    )

    row = qdb.list_intents(limit=5)[0]
    assert row["status"] == "filled"
    assert row["client_order_id"] == "cid-5"
    assert row["exchange_order_id"] == "ord-5"
    assert row["qty"] == 0.5


def test_live_intent_queue_stale_writer_cannot_override_newer_committed_state(monkeypatch, tmp_path):
    queue_mod = _reload_queue(monkeypatch, tmp_path)
    qdb = queue_mod.LiveIntentQueueSQLite()

    qdb.upsert_intent(
        {
            "intent_id": "intent-stale",
            "created_ts": "2026-04-02T12:00:00Z",
            "ts": "2026-04-02T12:00:00Z",
            "source": "strategy",
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
        }
    )

    assert qdb.update_status("intent-stale", "submitted") is True

    observed = qdb.list_intents(limit=10)[0]["status"]
    assert observed == "submitted"

    con = queue_mod._connect()
    try:
        con.execute(
            "UPDATE live_trade_intents SET status=?, updated_ts=? WHERE intent_id=?",
            ("held", queue_mod._now(), "intent-stale"),
        )
        con.commit()
    finally:
        con.close()

    assert qdb.update_status("intent-stale", "filled") is False

    row = qdb.list_intents(limit=10)[0]
    assert row["status"] == "held"


def test_live_intent_queue_atomic_risk_claim_enforces_limits(monkeypatch, tmp_path):
    queue_mod = _reload_queue(monkeypatch, tmp_path)
    qdb = queue_mod.LiveIntentQueueSQLite()

    ok1, reason1 = qdb.atomic_risk_claim(
        max_trades=1,
        max_notional=100.0,
        notional_est=40.0,
    )
    ok2, reason2 = qdb.atomic_risk_claim(
        max_trades=1,
        max_notional=100.0,
        notional_est=10.0,
    )

    assert (ok1, reason1) == (True, None)
    assert (ok2, reason2) == (False, "risk:max_trades_per_day")
    assert qdb.get_state("risk:trades") == "1"
    assert qdb.get_state("risk:notional") == "40.0"
