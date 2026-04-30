from __future__ import annotations

import importlib


def _reload_paper_flow_modules():
    import services.os.app_paths as app_paths
    import services.admin.config_editor as config_editor
    import storage.intent_queue_sqlite as intent_queue_sqlite
    import storage.paper_trading_sqlite as paper_trading_sqlite
    import storage.trade_journal_sqlite as trade_journal_sqlite
    import services.execution.paper_engine as paper_engine
    import services.execution.intent_reconciler as intent_reconciler
    import services.execution.paper_runner as paper_runner

    importlib.reload(app_paths)
    importlib.reload(config_editor)
    importlib.reload(intent_queue_sqlite)
    importlib.reload(paper_trading_sqlite)
    importlib.reload(trade_journal_sqlite)
    importlib.reload(paper_engine)
    importlib.reload(intent_reconciler)
    importlib.reload(paper_runner)
    return intent_queue_sqlite, trade_journal_sqlite, paper_engine, intent_reconciler, paper_runner


def test_queued_strategy_intent_becomes_journaled_paper_fill(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    intent_queue_sqlite, trade_journal_sqlite, paper_engine, intent_reconciler, paper_runner = _reload_paper_flow_modules()

    paper_cfg = {
        "paper_trading": {
            "starting_cash_quote": 1000.0,
            "fee_bps": 0.0,
            "slippage_bps": 0.0,
            "use_ccxt_fallback": False,
        }
    }
    monkeypatch.setattr(paper_engine, "load_user_yaml", lambda: paper_cfg)
    monkeypatch.setattr(paper_engine.PaperEngine, "_price", lambda self, venue, symbol: {"ts_ms": 1, "bid": 100.0, "ask": 100.0, "last": 100.0})
    monkeypatch.setattr(paper_engine, "is_snapshot_fresh", lambda: (True, None))
    monkeypatch.setattr(paper_engine, "is_master_read_only", lambda: (False, {}))
    monkeypatch.setattr(
        paper_engine,
        "check_market_quality",
        lambda venue, symbol: {"ok": True, "reason": "ok", "price_used": 100.0},
    )
    monkeypatch.setattr(paper_engine, "should_allow_order", lambda *args, **kwargs: (True, "ok"))

    qdb = intent_queue_sqlite.IntentQueueSQLite()
    jdb = trade_journal_sqlite.TradeJournalSQLite()
    eng = paper_engine.PaperEngine()

    qdb.upsert_intent(
        {
            "intent_id": "intent-1",
            "created_ts": "2026-03-19T12:00:00Z",
            "ts": "2026-03-19T12:00:00Z",
            "source": "strategy",
            "strategy_id": "ema_cross",
            "venue": "coinbase",
            "symbol": "BTC/USD",
            "side": "buy",
            "order_type": "market",
            "qty": 1.0,
            "limit_price": None,
            "status": "queued",
            "last_error": None,
            "client_order_id": None,
            "linked_order_id": None,
        }
    )

    queue_cycle = paper_runner._consume_queued_intents_once(qdb=qdb, eng=eng, limit=10)
    fill_cycle = eng.evaluate_open_orders()
    recon_cycle = intent_reconciler.reconcile_once(qdb=qdb, pdb=eng.db, jdb=jdb, max_intents=10)

    intent = qdb.get_intent("intent-1")
    fills = jdb.list_fills(limit=10)

    assert queue_cycle == {"queued_seen": 1, "submitted": 1, "rejected": 0, "idempotent": 0}
    assert fill_cycle["open_orders_seen"] == 1
    assert fill_cycle["filled"] == 1
    assert recon_cycle["fills_journaled"] == 1
    assert intent is not None
    assert intent["status"] == "filled"
    assert intent["client_order_id"] == "paper_intent_intent-1"
    assert intent["linked_order_id"]
    assert len(fills) == 1
    assert fills[0]["strategy_id"] == "ema_cross"
    assert fills[0]["intent_id"] == "intent-1"
    assert fills[0]["client_order_id"] == "paper_intent_intent-1"
