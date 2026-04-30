"""
tests/test_paper_reconciler_recovery.py

SQLite-backed integration tests for paper queue/reconciler recovery paths.

Covers:
- submitting -> rejected  (crash-recovery: claim sets submitting, submit fails, reconciler sees rejected order)
- submitted -> filled     (normal reconciliation round-trip through real DBs)
- submitted, order still new (reconciler must skip — no state change)
- submitted, linked_order_id missing (reconciler must skip — no state change)
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path


# ---------------------------------------------------------------------------
# Module reload helpers (mirrors test_paper_engine_integration.py pattern)
# ---------------------------------------------------------------------------

def _reload_modules(tmp_path: Path):
    import services.os.app_paths as app_paths
    import services.admin.config_editor as config_editor
    import storage.paper_trading_sqlite as paper_store
    import storage.intent_queue_sqlite as intent_queue
    import storage.trade_journal_sqlite as trade_journal
    import services.execution.paper_engine as paper_engine
    import services.execution.intent_reconciler as reconciler

    importlib.reload(app_paths)
    importlib.reload(config_editor)
    importlib.reload(paper_store)
    importlib.reload(intent_queue)
    importlib.reload(trade_journal)
    importlib.reload(paper_engine)
    importlib.reload(reconciler)

    return paper_store, intent_queue, trade_journal, paper_engine, reconciler


def _allow_submit_gates(monkeypatch, paper_engine):
    monkeypatch.setattr(paper_engine, "is_snapshot_fresh", lambda: (True, None))
    monkeypatch.setattr(paper_engine, "is_master_read_only", lambda: (False, {}))
    monkeypatch.setattr(
        paper_engine,
        "check_market_quality",
        lambda venue, symbol: {"ok": True, "reason": "ok", "price_used": 100.0},
    )
    monkeypatch.setattr(paper_engine, "should_allow_order", lambda *args, **kwargs: (True, "ok"))


def _base_intent(intent_id: str, status: str = "queued", linked_order_id: str | None = None) -> dict:
    return {
        "intent_id": intent_id,
        "created_ts": "2026-01-01T00:00:00+00:00",
        "ts": "2026-01-01T00:00:00+00:00",
        "source": "strategy",
        "strategy_id": "es_daily_trend_v1",
        "venue": "coinbase",
        "symbol": "BTC/USD",
        "side": "buy",
        "order_type": "market",
        "qty": 1.0,
        "limit_price": None,
        "status": status,
        "last_error": None,
        "client_order_id": f"paper_intent_{intent_id}",
        "linked_order_id": linked_order_id,
        "meta": None,
    }


# ---------------------------------------------------------------------------
# Test: submitting -> rejected
#
# Simulates crash-recovery: intent was claimed (status='submitting'),
# the paper order was rejected (insufficient_cash), reconciler must
# transition intent to 'rejected'.
# ---------------------------------------------------------------------------

def test_submitting_intent_transitions_to_rejected_when_order_rejected(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    paper_store, intent_queue, trade_journal, paper_engine, reconciler = _reload_modules(tmp_path)
    _allow_submit_gates(monkeypatch, paper_engine)

    qdb = intent_queue.IntentQueueSQLite()
    eng = paper_engine.PaperEngine()
    jdb = trade_journal.TradeJournalSQLite()

    # Seed: intent in 'queued', then claim atomically to 'submitting'
    qdb.upsert_intent(_base_intent("intent-sub-reject"))
    claimed = qdb.claim_next_queued(limit=1)
    assert len(claimed) == 1
    intent_id = claimed[0]["intent_id"]
    client_order_id = claimed[0]["client_order_id"]

    # Manually insert a rejected paper order (simulates crash-after-submit-before-queue-update)
    order_id = "order-rejected-001"
    eng.db.insert_order({
        "order_id": order_id,
        "client_order_id": client_order_id,
        "ts": "2026-01-01T00:00:00+00:00",
        "venue": "coinbase",
        "symbol": "BTC/USD",
        "side": "buy",
        "order_type": "market",
        "qty": 1.0,
        "limit_price": None,
        "status": "rejected",
        "reject_reason": "insufficient_cash",
        "strategy_id": "es_daily_trend_v1",
        "meta": None,
    })

    # Manually advance intent from 'submitting' to 'submitted' with linked_order_id
    qdb.update_status(intent_id, "submitted", client_order_id=client_order_id, linked_order_id=order_id)

    row = qdb.get_intent(intent_id)
    assert row["status"] == "submitted"
    assert row["linked_order_id"] == order_id

    # Reconciler runs: sees submitted intent, looks up rejected order
    out = reconciler.reconcile_once(qdb=qdb, pdb=eng.db, jdb=jdb, max_intents=50)

    assert out["intents_updated"] == 1
    assert out["fills_journaled"] == 0

    final = qdb.get_intent(intent_id)
    assert final["status"] == "rejected"
    assert final["last_error"] == "insufficient_cash"


# ---------------------------------------------------------------------------
# Test: submitted -> filled
#
# Normal round-trip: intent submitted, paper order fills via evaluate_open_orders,
# reconciler journals the fill and transitions intent to 'filled'.
# ---------------------------------------------------------------------------

def test_submitted_intent_transitions_to_filled_and_journals_fill(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    paper_store, intent_queue, trade_journal, paper_engine, reconciler = _reload_modules(tmp_path)
    _allow_submit_gates(monkeypatch, paper_engine)

    qdb = intent_queue.IntentQueueSQLite()
    jdb = trade_journal.TradeJournalSQLite()
    eng = paper_engine.PaperEngine()

    monkeypatch.setattr(
        paper_engine.PaperEngine,
        "_price",
        lambda self, venue, symbol: {"ts_ms": 1, "bid": 100.0, "ask": 100.0, "last": 100.0},
    )

    # Submit via paper engine
    resp = eng.submit_order(
        client_order_id="paper_intent_intent-sub-fill",
        venue="coinbase",
        symbol="BTC/USD",
        side="buy",
        order_type="market",
        qty=1.0,
    )
    assert resp["ok"] is True
    order_id = resp["order"]["order_id"]

    # Seed intent in 'submitted' with linked_order_id
    qdb.upsert_intent(_base_intent("intent-sub-fill", status="submitted", linked_order_id=order_id))
    row = qdb.get_intent("intent-sub-fill")
    assert row["status"] == "submitted"

    # Order is still 'new' — reconciler must skip
    out_pre = reconciler.reconcile_once(qdb=qdb, pdb=eng.db, jdb=jdb, max_intents=50)
    assert out_pre["intents_updated"] == 0
    assert qdb.get_intent("intent-sub-fill")["status"] == "submitted"

    # Fill the order via evaluate_open_orders
    fill_result = eng.evaluate_open_orders()
    assert fill_result["filled"] == 1

    order = eng.db.get_order_by_client_id("paper_intent_intent-sub-fill")
    assert order["status"] == "filled"

    # Reconciler runs: sees filled order, journals fill, transitions intent
    out = reconciler.reconcile_once(qdb=qdb, pdb=eng.db, jdb=jdb, max_intents=50)

    assert out["intents_updated"] == 1
    assert out["fills_journaled"] == 1

    final = qdb.get_intent("intent-sub-fill")
    assert final["status"] == "filled"
    assert jdb.count() == 1


# ---------------------------------------------------------------------------
# Test: submitted intent with order still 'new' — reconciler must skip
#
# Reconciler must not change intent status when paper order is still open.
# ---------------------------------------------------------------------------

def test_submitted_intent_skipped_when_order_still_new(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    paper_store, intent_queue, trade_journal, paper_engine, reconciler = _reload_modules(tmp_path)
    _allow_submit_gates(monkeypatch, paper_engine)

    qdb = intent_queue.IntentQueueSQLite()
    jdb = trade_journal.TradeJournalSQLite()
    eng = paper_engine.PaperEngine()

    resp = eng.submit_order(
        client_order_id="paper_intent_intent-pending",
        venue="coinbase",
        symbol="BTC/USD",
        side="buy",
        order_type="limit",
        qty=1.0,
        limit_price=50.0,   # below market — will not fill
    )
    assert resp["ok"] is True
    order_id = resp["order"]["order_id"]

    qdb.upsert_intent(_base_intent("intent-pending", status="submitted", linked_order_id=order_id))

    out = reconciler.reconcile_once(qdb=qdb, pdb=eng.db, jdb=jdb, max_intents=50)

    assert out["intents_updated"] == 0
    assert qdb.get_intent("intent-pending")["status"] == "submitted"


# ---------------------------------------------------------------------------
# Test: submitted intent missing linked_order_id — reconciler must skip
# ---------------------------------------------------------------------------

def test_submitted_intent_without_linked_order_id_is_skipped(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    paper_store, intent_queue, trade_journal, paper_engine, reconciler = _reload_modules(tmp_path)

    qdb = intent_queue.IntentQueueSQLite()
    jdb = trade_journal.TradeJournalSQLite()
    pdb = paper_store.PaperTradingSQLite()

    qdb.upsert_intent(_base_intent("intent-no-link", status="submitted", linked_order_id=None))

    out = reconciler.reconcile_once(qdb=qdb, pdb=pdb, jdb=jdb, max_intents=50)

    assert out["intents_updated"] == 0
    assert qdb.get_intent("intent-no-link")["status"] == "submitted"
