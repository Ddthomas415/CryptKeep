from __future__ import annotations

import importlib
import json


def _reload_paper_runner():
    import services.os.app_paths as app_paths
    import storage.intent_queue_sqlite as intent_queue_sqlite
    import storage.paper_trading_sqlite as paper_trading_sqlite
    import storage.trade_journal_sqlite as trade_journal_sqlite
    import services.execution.intent_reconciler as intent_reconciler
    import services.execution.paper_runner as paper_runner

    importlib.reload(app_paths)
    importlib.reload(intent_queue_sqlite)
    importlib.reload(paper_trading_sqlite)
    importlib.reload(trade_journal_sqlite)
    importlib.reload(intent_reconciler)
    importlib.reload(paper_runner)
    return paper_runner


def test_paper_runner_request_stop_writes_flag(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    paper_runner = _reload_paper_runner()

    out = paper_runner.request_stop()

    assert out["ok"] is True
    assert paper_runner.STOP_FILE.exists()


def test_paper_runner_run_forever_cycles_once_and_releases_lock(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    paper_runner = _reload_paper_runner()
    calls = {"evaluate": 0, "mtm": 0, "queue": 0, "reconcile": 0}

    class FakeEngine:
        db = object()

        def evaluate_open_orders(self) -> dict:
            calls["evaluate"] += 1
            return {"open_orders_seen": 0, "filled": 0, "rejected": 0}

        def mark_to_market(self, venue: str, symbol: str) -> dict:
            calls["mtm"] += 1
            return {
                "cash_quote": 1000.0,
                "equity_quote": 1000.0,
                "unrealized_pnl": 0.0,
                "realized_pnl": 0.0,
                "mid": 100.0,
            }

    def fake_consume(**_kwargs) -> dict:
        calls["queue"] += 1
        return {"queued_seen": 0, "submitted": 0, "rejected": 0, "idempotent": 0}

    def fake_reconcile(**_kwargs) -> dict:
        calls["reconcile"] += 1
        return {"submitted_checked": 0, "intents_updated": 0, "fills_journaled": 0, "journal_count": 0}

    def fake_sleep(_seconds: float) -> None:
        if not paper_runner.STOP_FILE.exists():
            paper_runner.STOP_FILE.parent.mkdir(parents=True, exist_ok=True)
            paper_runner.STOP_FILE.write_text("stop\n", encoding="utf-8")

    monkeypatch.setattr(paper_runner, "PaperEngine", FakeEngine)
    monkeypatch.setattr(
        paper_runner,
        "load_user_yaml",
        lambda: {"paper_trading": {"default_venue": "coinbase", "default_symbol": "BTC/USD", "loop_interval_sec": 0.0}},
    )
    monkeypatch.setattr(paper_runner, "_consume_queued_intents_once", fake_consume)
    monkeypatch.setattr(paper_runner, "reconcile_once", fake_reconcile)
    monkeypatch.setattr(paper_runner.time, "sleep", fake_sleep)

    paper_runner.run_forever()

    assert calls == {"evaluate": 1, "mtm": 1, "queue": 1, "reconcile": 1}
    assert not paper_runner.LOCK_FILE.exists()
    assert paper_runner.STATUS_FILE.exists()

    status = json.loads(paper_runner.STATUS_FILE.read_text(encoding="utf-8"))
    assert status["status"] == "stopped"


def test_consume_queued_intents_once_submits_and_links_order(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    paper_runner = _reload_paper_runner()
    qdb = paper_runner.IntentQueueSQLite()
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
            "qty": 0.5,
            "limit_price": None,
            "status": "queued",
            "last_error": None,
            "client_order_id": None,
            "linked_order_id": None,
        }
    )

    class FakeEngine:
        def submit_order(self, **kwargs) -> dict:
            assert kwargs["client_order_id"] == "paper_intent_intent-1"
            return {
                "ok": True,
                "idempotent": False,
                "order": {"order_id": "paper-order-1", "reject_reason": None},
            }

    out = paper_runner._consume_queued_intents_once(qdb=qdb, eng=FakeEngine(), limit=10)

    assert out == {"queued_seen": 1, "submitted": 1, "rejected": 0, "idempotent": 0}
    row = qdb.get_intent("intent-1")
    assert row is not None
    assert row["status"] == "submitted"
    assert row["client_order_id"] == "paper_intent_intent-1"
    assert row["linked_order_id"] == "paper-order-1"
