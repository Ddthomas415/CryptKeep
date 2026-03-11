from __future__ import annotations

import importlib


def _reload_state_modules(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths

    importlib.reload(app_paths)
    return app_paths


def test_intent_writer_mirrors_into_execution_queue(monkeypatch, tmp_path):
    _reload_state_modules(monkeypatch, tmp_path)
    import storage.intent_queue_sqlite as queue_mod
    import services.execution.intent_writer as writer_mod

    importlib.reload(queue_mod)
    importlib.reload(writer_mod)

    w = writer_mod.IntentWriter(writer_mod.IntentWriterCfg(exec_db=str(tmp_path / "exec.sqlite")))
    intent_id = w.create_intent(
        exchange="coinbase",
        symbol="BTC/USD",
        mode="paper",
        side="buy",
        qty=0.1,
        order_type="market",
        price=None,
        meta={"strategy": "ema_crossover_v1"},
        status="pending",
        strategy_id="ema_crossover_v1",
        source="pipeline",
        enqueue_execution=True,
    )

    p = w.get_intent(intent_id)
    assert p is not None
    assert p["status"] == "pending"
    assert p["symbol"] == "BTC/USD"

    q = queue_mod.IntentQueueSQLite().get_intent(intent_id)
    assert q is not None
    assert q["status"] == "queued"
    assert q["source"] == "pipeline"
    assert q["strategy_id"] == "ema_crossover_v1"


def test_intent_writer_mark_status_updates_queue(monkeypatch, tmp_path):
    _reload_state_modules(monkeypatch, tmp_path)
    import storage.intent_queue_sqlite as queue_mod
    import services.execution.intent_writer as writer_mod

    importlib.reload(queue_mod)
    importlib.reload(writer_mod)

    w = writer_mod.IntentWriter(writer_mod.IntentWriterCfg(exec_db=str(tmp_path / "exec.sqlite")))
    intent_id = w.create_intent(
        exchange="coinbase",
        symbol="ETH/USD",
        mode="paper",
        side="sell",
        qty=0.2,
        order_type="market",
        price=None,
        meta={},
        status="pending",
        enqueue_execution=True,
    )
    w.mark_status(intent_id, status="submitted", last_error=None)

    p = w.get_intent(intent_id)
    q = queue_mod.IntentQueueSQLite().get_intent(intent_id)
    assert p is not None and p["status"] == "submitted"
    assert q is not None and q["status"] == "submitted"

