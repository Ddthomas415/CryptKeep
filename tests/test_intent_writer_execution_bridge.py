from __future__ import annotations

import importlib

import pytest


def _reload_modules(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    import services.os.app_paths as app_paths
    import storage.intent_queue_sqlite as queue_mod
    import services.execution.intent_writer as writer_mod

    importlib.reload(app_paths)
    importlib.reload(queue_mod)
    importlib.reload(writer_mod)

    return queue_mod, writer_mod


def test_intent_writer_mirrors_into_execution_queue(monkeypatch, tmp_path):
    queue_mod, writer_mod = _reload_modules(monkeypatch, tmp_path)

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

    q = writer_mod.IntentQueueSQLite().get_intent(intent_id)
    assert q is not None
    assert q["status"] == "queued"
    assert q["source"] == "pipeline"
    assert q["strategy_id"] == "ema_crossover_v1"


def test_intent_writer_mark_status_updates_queue(monkeypatch, tmp_path):
    queue_mod, writer_mod = _reload_modules(monkeypatch, tmp_path)

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
    q = writer_mod.IntentQueueSQLite().get_intent(intent_id)
    assert p is not None and p["status"] == "submitted"
    assert q is not None and q["status"] == "submitted"


def test_create_intent_mirror_failure_raises(monkeypatch, tmp_path):
    queue_mod, writer_mod = _reload_modules(monkeypatch, tmp_path)

    def _fail_upsert(self, row):
        raise RuntimeError("simulated queue write failure")

    monkeypatch.setattr(writer_mod.IntentQueueSQLite, "upsert_intent", _fail_upsert)

    w = writer_mod.IntentWriter(writer_mod.IntentWriterCfg(exec_db=str(tmp_path / "exec.sqlite")))

    with pytest.raises(RuntimeError, match="queue mirror failed"):
        w.create_intent(
            exchange="coinbase",
            symbol="BTC/USD",
            mode="paper",
            side="buy",
            qty=0.1,
            order_type="market",
            price=None,
            enqueue_execution=True,
        )


def test_mark_status_mirror_failure_raises(monkeypatch, tmp_path):
    queue_mod, writer_mod = _reload_modules(monkeypatch, tmp_path)

    w = writer_mod.IntentWriter(writer_mod.IntentWriterCfg(exec_db=str(tmp_path / "exec.sqlite")))
    intent_id = w.create_intent(
        exchange="coinbase",
        symbol="ETH/USD",
        mode="paper",
        side="sell",
        qty=0.2,
        order_type="market",
        price=None,
        enqueue_execution=True,
    )

    def _fail_update(self, intent_id, status, **_kwargs):
        raise RuntimeError("simulated queue status write failure")

    monkeypatch.setattr(writer_mod.IntentQueueSQLite, "update_status", _fail_update)

    with pytest.raises(RuntimeError, match="queue status mirror failed"):
        w.mark_status(intent_id, status="submitted")


def test_create_intent_enqueue_false_skips_mirror(monkeypatch, tmp_path):
    queue_mod, writer_mod = _reload_modules(monkeypatch, tmp_path)

    upsert_calls = []

    def _track_upsert(self, row):
        upsert_calls.append(row)

    monkeypatch.setattr(writer_mod.IntentQueueSQLite, "upsert_intent", _track_upsert)

    w = writer_mod.IntentWriter(writer_mod.IntentWriterCfg(exec_db=str(tmp_path / "exec.sqlite")))
    intent_id = w.create_intent(
        exchange="coinbase",
        symbol="BTC/USD",
        mode="paper",
        side="buy",
        qty=0.1,
        order_type="market",
        price=None,
        enqueue_execution=False,
    )

    assert intent_id is not None
    assert upsert_calls == []
