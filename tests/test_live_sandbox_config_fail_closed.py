from __future__ import annotations

from services.config_loader import ConfigLoadError


def _intent() -> dict:
    return {
        "intent_id": "intent-1",
        "venue": "coinbase",
        "symbol": "BTC/USD",
        "exchange_order_id": "ord-1",
        "client_order_id": "cid-1",
        "side": "buy",
        "order_type": "limit",
        "qty": 0.1,
        "limit_price": 100.0,
        "created_ts": "2026-01-01T00:00:00+00:00",
        "updated_ts": "2026-01-01T00:00:00+00:00",
        "meta": {},
    }


def _raise_config_load_error(**kwargs):
    assert kwargs == {"strict": True}
    raise ConfigLoadError("config_load_failed:/tmp/user.yaml:ScannerError:bad")


def test_live_reconciler_sandbox_config_load_error_blocks_adapter(monkeypatch, tmp_path):
    import services.execution.live_reconciler as reconciler

    statuses: list[dict] = []
    adapter_calls: list[tuple] = []

    class FakeQueue:
        def list_intents(self, *, limit: int = 60, status: str):
            return [_intent()] if status == "submitted" else []

    class FakeTrading:
        pass

    def _adapter(*args, **kwargs):
        adapter_calls.append((args, kwargs))
        raise AssertionError("adapter should not be created when sandbox config is untrusted")

    monkeypatch.setattr(reconciler, "STOP_FILE", tmp_path / "live_reconciler.stop")
    monkeypatch.setattr(reconciler, "FLAGS", tmp_path)
    monkeypatch.setattr(reconciler, "LOCKS", tmp_path)
    monkeypatch.setattr(reconciler, "STATUS_FILE", tmp_path / "live_reconciler.status.json")
    monkeypatch.setattr(reconciler, "LOCK_FILE", tmp_path / "live_reconciler.lock")
    monkeypatch.setattr(reconciler, "ensure_dirs", lambda: None)
    monkeypatch.setattr(reconciler, "_acquire_lock", lambda: True)
    monkeypatch.setattr(reconciler, "_release_lock", lambda: None)
    monkeypatch.setattr(reconciler, "_write_status", lambda obj: statuses.append(dict(obj)))
    monkeypatch.setattr(reconciler, "get_system_guard_state", lambda **_: {"state": "RUNNING"})
    monkeypatch.setattr(reconciler, "live_enabled_and_armed", lambda: (True, "armed"))
    monkeypatch.setattr(reconciler, "load_runtime_trading_config", _raise_config_load_error)
    monkeypatch.setattr(reconciler, "LiveIntentQueueSQLite", lambda: FakeQueue())
    monkeypatch.setattr(reconciler, "LiveTradingSQLite", lambda: FakeTrading())
    monkeypatch.setattr(reconciler, "LiveExchangeAdapter", _adapter)

    def _sleep(_seconds: float):
        reconciler.STOP_FILE.write_text("stop\n", encoding="utf-8")

    monkeypatch.setattr(reconciler.time, "sleep", _sleep)

    reconciler.run_forever()

    assert adapter_calls == []
    assert any(
        status.get("status") == "blocked"
        and status.get("reason") == "config_load_failed"
        and status.get("error") == "config_load_failed:ConfigLoadError"
        for status in statuses
    )


def test_live_intent_consumer_sandbox_config_load_error_blocks_claim_and_adapter(monkeypatch, tmp_path):
    import services.execution.live_intent_consumer as consumer

    statuses: list[dict] = []
    adapter_calls: list[tuple] = []
    claim_calls: list[str] = []

    class FakeQueue:
        def list_intents(self, *, limit: int = 200, status: str):
            assert status == "submitting"
            return []

        def claim_next_queued(self, *, limit: int = 10):
            claim_calls.append("claim_next_queued")
            raise AssertionError("queued intents must not be claimed when sandbox config is untrusted")

    class FakeTrading:
        pass

    class FakeDedupe:
        pass

    def _adapter(*args, **kwargs):
        adapter_calls.append((args, kwargs))
        raise AssertionError("adapter should not be created when sandbox config is untrusted")

    monkeypatch.setattr(consumer, "STOP_FILE", tmp_path / "live_intent_consumer.stop")
    monkeypatch.setattr(consumer, "FLAGS", tmp_path)
    monkeypatch.setattr(consumer, "LOCKS", tmp_path)
    monkeypatch.setattr(consumer, "STATUS_FILE", tmp_path / "live_intent_consumer.status.json")
    monkeypatch.setattr(consumer, "LOCK_FILE", tmp_path / "live_intent_consumer.lock")
    monkeypatch.setattr(consumer, "ensure_dirs", lambda: None)
    monkeypatch.setattr(consumer, "_acquire_lock", lambda: True)
    monkeypatch.setattr(consumer, "_release_lock", lambda: None)
    monkeypatch.setattr(consumer, "_write_status", lambda obj: statuses.append(dict(obj)))
    monkeypatch.setattr(consumer, "live_enabled_and_armed", lambda: (True, "armed"))
    monkeypatch.setattr(consumer, "is_snapshot_fresh", lambda: (True, "fresh"))
    monkeypatch.setattr(consumer, "load_runtime_trading_config", _raise_config_load_error)
    monkeypatch.setattr(consumer, "LiveIntentQueueSQLite", lambda: FakeQueue())
    monkeypatch.setattr(consumer, "LiveTradingSQLite", lambda: FakeTrading())
    monkeypatch.setattr(consumer, "OrderDedupeStore", lambda: FakeDedupe())
    monkeypatch.setattr(consumer, "LiveExchangeAdapter", _adapter)

    def _sleep(_seconds: float):
        consumer.STOP_FILE.write_text("stop\n", encoding="utf-8")

    monkeypatch.setattr(consumer.time, "sleep", _sleep)

    consumer.run_forever()

    assert claim_calls == []
    assert adapter_calls == []
    assert any(
        status.get("status") == "blocked"
        and status.get("reason") == "config_load_failed"
        and status.get("error") == "config_load_failed:ConfigLoadError"
        for status in statuses
    )


def test_live_intent_consumer_stale_recovery_leaves_rows_untouched_on_config_error(monkeypatch):
    import services.execution.live_intent_consumer as consumer

    adapter_calls: list[tuple] = []

    class FakeQueue:
        def list_intents(self, *, limit: int = 200, status: str):
            assert status == "submitting"
            return [_intent()]

    def _adapter(*args, **kwargs):
        adapter_calls.append((args, kwargs))
        raise AssertionError("adapter should not be created when sandbox config is untrusted")

    monkeypatch.setattr(consumer, "load_runtime_trading_config", _raise_config_load_error)
    monkeypatch.setattr(consumer, "LiveExchangeAdapter", _adapter)

    out = consumer._recover_stale_submitting(FakeQueue(), object(), object())

    assert adapter_calls == []
    assert out["scanned"] == 1
    assert out["left_untouched"] == 1
    assert out["config_load_failed"] == 1


def test_compat_intent_consumer_sandbox_config_load_error_blocks_adapter(monkeypatch, tmp_path):
    import services.execution.intent_consumer as consumer

    statuses: list[dict] = []
    adapter_calls: list[tuple] = []

    class FakeQueue:
        def next_queued(self, *, limit: int = 10):
            return [_intent()]

    class FakeTrading:
        pass

    def _adapter(*args, **kwargs):
        adapter_calls.append((args, kwargs))
        raise AssertionError("adapter should not be created when sandbox config is untrusted")

    monkeypatch.setattr(consumer, "STOP_FILE", tmp_path / "intent_consumer.stop")
    monkeypatch.setattr(consumer, "FLAGS", tmp_path)
    monkeypatch.setattr(consumer, "LOCKS", tmp_path)
    monkeypatch.setattr(consumer, "STATUS_FILE", tmp_path / "intent_consumer.status.json")
    monkeypatch.setattr(consumer, "LOCK_FILE", tmp_path / "intent_consumer.lock")
    monkeypatch.setattr(consumer, "ensure_dirs", lambda: None)
    monkeypatch.setattr(consumer, "_acquire_lock", lambda: True)
    monkeypatch.setattr(consumer, "_release_lock", lambda: None)
    monkeypatch.setattr(consumer, "_write_status", lambda obj: statuses.append(dict(obj)))
    monkeypatch.setattr(consumer, "live_enabled_and_armed", lambda: (True, "armed"))
    monkeypatch.setattr(consumer, "is_snapshot_fresh", lambda: (True, "fresh"))
    monkeypatch.setattr(consumer, "load_runtime_trading_config", _raise_config_load_error)
    monkeypatch.setattr(consumer, "LiveIntentQueueSQLite", lambda: FakeQueue())
    monkeypatch.setattr(consumer, "LiveTradingSQLite", lambda: FakeTrading())
    monkeypatch.setattr(consumer, "LiveExchangeAdapter", _adapter)

    def _sleep(_seconds: float):
        consumer.STOP_FILE.write_text("stop\n", encoding="utf-8")

    monkeypatch.setattr(consumer.time, "sleep", _sleep)

    consumer.run_forever()

    assert adapter_calls == []
    assert any(
        status.get("status") == "blocked"
        and status.get("reason") == "config_load_failed"
        and status.get("error") == "config_load_failed:ConfigLoadError"
        for status in statuses
    )
