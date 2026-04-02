from __future__ import annotations

from services.execution import live_reconciler as lr


def test_live_reconciler_reuses_adapter_per_venue_within_single_pass(monkeypatch, tmp_path):
    stop_file = tmp_path / "live_reconciler.stop"

    statuses: list[dict] = []
    queue_updates: list[tuple[str, str, str | None]] = []

    class _FakeQueue:
        def __init__(self):
            self.state: dict[str, str] = {}

        def list_intents(self, *, limit: int = 60, status: str):
            assert status == "submitted"
            return [
                {
                    "intent_id": "intent-1",
                    "venue": "coinbase",
                    "symbol": "BTC/USD",
                    "exchange_order_id": "ord-1",
                    "client_order_id": "cid-1",
                    "side": "buy",
                    "order_type": "limit",
                    "qty": 0.1,
                    "limit_price": 100.0,
                },
                {
                    "intent_id": "intent-2",
                    "venue": "coinbase",
                    "symbol": "ETH/USD",
                    "exchange_order_id": "ord-2",
                    "client_order_id": "cid-2",
                    "side": "sell",
                    "order_type": "limit",
                    "qty": 0.2,
                    "limit_price": 200.0,
                },
            ]

        def update_status(self, intent_id: str, status: str, last_error: str | None = None):
            queue_updates.append((intent_id, status, last_error))

        def get_state(self, key: str):
            return self.state.get(key, "0")

        def set_state(self, key: str, value: str):
            self.state[key] = value

    class _FakeTrading:
        def __init__(self):
            self.orders: list[dict] = []
            self.fills: list[dict] = []

        def upsert_order(self, row: dict):
            self.orders.append(dict(row))

        def insert_fill(self, row: dict):
            self.fills.append(dict(row))

    instances: list["_FakeAdapter"] = []

    class _FakeAdapter:
        def __init__(self, venue: str):
            self.venue = venue
            self.fetch_order_calls: list[tuple[str, str]] = []
            self.fetch_trade_calls: list[tuple[str, int | None, int | None]] = []
            self.close_calls = 0
            instances.append(self)

        def fetch_order(self, canonical_symbol: str, exchange_order_id: str):
            self.fetch_order_calls.append((canonical_symbol, exchange_order_id))
            return {"id": exchange_order_id, "status": "open"}

        def fetch_my_trades(self, canonical_symbol: str, since_ms: int | None = None, limit: int | None = 200):
            self.fetch_trade_calls.append((canonical_symbol, since_ms, limit))
            return []

        def close(self):
            self.close_calls += 1

    monkeypatch.setattr(lr, "STOP_FILE", stop_file)
    monkeypatch.setattr(lr, "FLAGS", tmp_path)
    monkeypatch.setattr(lr, "LOCKS", tmp_path)
    monkeypatch.setattr(lr, "STATUS_FILE", tmp_path / "live_reconciler.status.json")
    monkeypatch.setattr(lr, "LOCK_FILE", tmp_path / "live_reconciler.lock")
    monkeypatch.setattr(lr, "ensure_dirs", lambda: None)
    monkeypatch.setattr(lr, "_acquire_lock", lambda: True)
    monkeypatch.setattr(lr, "_release_lock", lambda: None)
    monkeypatch.setattr(lr, "_write_status", lambda obj: statuses.append(dict(obj)))
    monkeypatch.setattr(lr, "get_system_guard_state", lambda **_: {"state": "RUNNING", "writer": "test", "reason": "ok"})
    monkeypatch.setattr(lr, "live_enabled_and_armed", lambda: (True, "armed"))
    monkeypatch.setattr(lr, "LiveIntentQueueSQLite", lambda: _FakeQueue())
    monkeypatch.setattr(lr, "LiveTradingSQLite", lambda: _FakeTrading())
    monkeypatch.setattr(lr, "LiveExchangeAdapter", _FakeAdapter)

    def _sleep(_seconds: float):
        if not stop_file.exists():
            stop_file.write_text("stop\n", encoding="utf-8")

    monkeypatch.setattr(lr.time, "sleep", _sleep)

    lr.run_forever()

    assert len(instances) == 1
    assert instances[0].venue == "coinbase"
    assert instances[0].fetch_order_calls == [("BTC/USD", "ord-1"), ("ETH/USD", "ord-2")]
    assert [call[0] for call in instances[0].fetch_trade_calls] == ["BTC/USD", "ETH/USD"]
    assert instances[0].close_calls == 1
    assert queue_updates == []
    assert any(item.get("status") == "stopped" for item in statuses)


def test_live_reconciler_guard_halting_allows_cleanup_when_not_armed(monkeypatch, tmp_path):
    stop_file = tmp_path / "live_reconciler.stop"
    statuses: list[dict] = []
    instances: list["_FakeAdapter"] = []

    class _FakeQueue:
        def __init__(self):
            self.state: dict[str, str] = {}

        def list_intents(self, *, limit: int = 60, status: str):
            assert status == "submitted"
            return [
                {
                    "intent_id": "intent-1",
                    "venue": "coinbase",
                    "symbol": "BTC/USD",
                    "exchange_order_id": "ord-1",
                    "client_order_id": "cid-1",
                    "side": "buy",
                    "order_type": "limit",
                    "qty": 0.1,
                    "limit_price": 100.0,
                }
            ]

        def update_status(self, intent_id: str, status: str, last_error: str | None = None):
            return None

        def get_state(self, key: str):
            return self.state.get(key, "0")

        def set_state(self, key: str, value: str):
            self.state[key] = value

    class _FakeTrading:
        def upsert_order(self, row: dict):
            return None

        def insert_fill(self, row: dict):
            return None

    class _FakeAdapter:
        def __init__(self, venue: str):
            self.venue = venue
            self.close_calls = 0
            instances.append(self)

        def fetch_order(self, canonical_symbol: str, exchange_order_id: str):
            return {"id": exchange_order_id, "status": "open"}

        def fetch_my_trades(self, canonical_symbol: str, since_ms: int | None = None, limit: int | None = 200):
            return []

        def close(self):
            self.close_calls += 1

    monkeypatch.setattr(lr, "STOP_FILE", stop_file)
    monkeypatch.setattr(lr, "FLAGS", tmp_path)
    monkeypatch.setattr(lr, "LOCKS", tmp_path)
    monkeypatch.setattr(lr, "STATUS_FILE", tmp_path / "live_reconciler.status.json")
    monkeypatch.setattr(lr, "LOCK_FILE", tmp_path / "live_reconciler.lock")
    monkeypatch.setattr(lr, "ensure_dirs", lambda: None)
    monkeypatch.setattr(lr, "_acquire_lock", lambda: True)
    monkeypatch.setattr(lr, "_release_lock", lambda: None)
    monkeypatch.setattr(lr, "_write_status", lambda obj: statuses.append(dict(obj)))
    monkeypatch.setattr(lr, "get_system_guard_state", lambda **_: {"state": "HALTING", "writer": "watchdog", "reason": "stale"})
    guard_calls: list[tuple[str, str, str]] = []
    monkeypatch.setattr(
        lr,
        "set_system_guard_state",
        lambda state, *, writer, reason="": guard_calls.append((state, writer, reason)) or {"state": state, "writer": writer, "reason": reason},
    )
    monkeypatch.setattr(lr, "live_enabled_and_armed", lambda: (False, "not_armed"))
    monkeypatch.setattr(lr, "LiveIntentQueueSQLite", lambda: _FakeQueue())
    monkeypatch.setattr(lr, "LiveTradingSQLite", lambda: _FakeTrading())
    monkeypatch.setattr(lr, "LiveExchangeAdapter", _FakeAdapter)

    def _sleep(_seconds: float):
        if not stop_file.exists():
            stop_file.write_text("stop\n", encoding="utf-8")

    monkeypatch.setattr(lr.time, "sleep", _sleep)

    lr.run_forever()

    assert len(instances) == 1
    assert instances[0].close_calls == 1
    assert any(item.get("status") == "halting" and item.get("reconcile_mode") == "cleanup" for item in statuses)
    assert guard_calls == []


def test_live_reconciler_guard_halted_reports_cleanup_without_arming(monkeypatch, tmp_path):
    stop_file = tmp_path / "live_reconciler.stop"
    statuses: list[dict] = []

    class _FakeQueue:
        def list_intents(self, *, limit: int = 60, status: str):
            assert status == "submitted"
            return []

    class _FakeTrading:
        pass

    monkeypatch.setattr(lr, "STOP_FILE", stop_file)
    monkeypatch.setattr(lr, "FLAGS", tmp_path)
    monkeypatch.setattr(lr, "LOCKS", tmp_path)
    monkeypatch.setattr(lr, "STATUS_FILE", tmp_path / "live_reconciler.status.json")
    monkeypatch.setattr(lr, "LOCK_FILE", tmp_path / "live_reconciler.lock")
    monkeypatch.setattr(lr, "ensure_dirs", lambda: None)
    monkeypatch.setattr(lr, "_acquire_lock", lambda: True)
    monkeypatch.setattr(lr, "_release_lock", lambda: None)
    monkeypatch.setattr(lr, "_write_status", lambda obj: statuses.append(dict(obj)))
    monkeypatch.setattr(lr, "get_system_guard_state", lambda **_: {"state": "HALTED", "writer": "operator", "reason": "manual"})
    monkeypatch.setattr(lr, "live_enabled_and_armed", lambda: (False, "not_armed"))
    monkeypatch.setattr(lr, "LiveIntentQueueSQLite", lambda: _FakeQueue())
    monkeypatch.setattr(lr, "LiveTradingSQLite", lambda: _FakeTrading())

    def _sleep(_seconds: float):
        if not stop_file.exists():
            stop_file.write_text("stop\n", encoding="utf-8")

    monkeypatch.setattr(lr.time, "sleep", _sleep)

    lr.run_forever()

    assert any(item.get("status") == "halted" and item.get("reconcile_mode") == "cleanup" for item in statuses)


def test_live_reconciler_promotes_halting_to_halted_when_cleanup_complete(monkeypatch, tmp_path):
    stop_file = tmp_path / "live_reconciler.stop"
    statuses: list[dict] = []
    guard_calls: list[tuple[str, str, str]] = []

    class _FakeQueue:
        def list_intents(self, *, limit: int = 60, status: str):
            assert status == "submitted"
            return []

    class _FakeTrading:
        pass

    monkeypatch.setattr(lr, "STOP_FILE", stop_file)
    monkeypatch.setattr(lr, "FLAGS", tmp_path)
    monkeypatch.setattr(lr, "LOCKS", tmp_path)
    monkeypatch.setattr(lr, "STATUS_FILE", tmp_path / "live_reconciler.status.json")
    monkeypatch.setattr(lr, "LOCK_FILE", tmp_path / "live_reconciler.lock")
    monkeypatch.setattr(lr, "ensure_dirs", lambda: None)
    monkeypatch.setattr(lr, "_acquire_lock", lambda: True)
    monkeypatch.setattr(lr, "_release_lock", lambda: None)
    monkeypatch.setattr(lr, "_write_status", lambda obj: statuses.append(dict(obj)))
    monkeypatch.setattr(lr, "get_system_guard_state", lambda **_: {"state": "HALTING", "writer": "watchdog", "reason": "stale"})
    monkeypatch.setattr(
        lr,
        "set_system_guard_state",
        lambda state, *, writer, reason="": guard_calls.append((state, writer, reason)) or {"state": state, "writer": writer, "reason": reason},
    )
    monkeypatch.setattr(lr, "live_enabled_and_armed", lambda: (False, "not_armed"))
    monkeypatch.setattr(lr, "LiveIntentQueueSQLite", lambda: _FakeQueue())
    monkeypatch.setattr(lr, "LiveTradingSQLite", lambda: _FakeTrading())

    def _sleep(_seconds: float):
        if not stop_file.exists():
            stop_file.write_text("stop\n", encoding="utf-8")

    monkeypatch.setattr(lr.time, "sleep", _sleep)

    lr.run_forever()

    assert guard_calls == [("HALTED", "live_reconciler", "cleanup_complete")]
    assert any(item.get("status") == "halted" and item.get("reconcile_mode") == "cleanup" for item in statuses)
