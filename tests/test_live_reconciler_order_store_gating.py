from services.execution import live_reconciler as lr


def test_filled_branch_does_not_upsert_order_when_queue_update_fails(monkeypatch, tmp_path):
    stop_file = tmp_path / "live_reconciler.stop"
    upserts = []

    class FakeQueue:
        def list_intents(self, *, limit=60, status):
            if status == "submit_unknown":
                return []
            return [
                {
                    "intent_id": "i1",
                    "venue": "coinbase",
                    "symbol": "BTC/USD",
                    "exchange_order_id": "ex-1",
                    "client_order_id": "cid-1",
                    "side": "buy",
                    "order_type": "limit",
                    "qty": 1.0,
                    "limit_price": 100.0,
                    "status": "submitted",
                    "updated_ts": "2026-01-01T00:00:00+00:00",
                }
            ]

        def update_status(self, *args, **kwargs):
            return False

        def get_state(self, key):
            return "0"

        def set_state(self, key, value):
            return None

    class FakeTrading:
        def upsert_order(self, row):
            upserts.append(dict(row))

        def insert_fill(self, row):
            return None

    class FakeAdapter:
        def __init__(self, venue, sandbox=False):
            pass

        def fetch_order(self, symbol, exchange_order_id):
            return {"id": exchange_order_id, "status": "filled"}

        def fetch_my_trades(self, symbol, since_ms=None, limit=200):
            return []

        def close(self):
            return None

    monkeypatch.setattr(lr, "STOP_FILE", stop_file)
    monkeypatch.setattr(lr, "FLAGS", tmp_path)
    monkeypatch.setattr(lr, "LOCKS", tmp_path)
    monkeypatch.setattr(lr, "STATUS_FILE", tmp_path / "live_reconciler.status.json")
    monkeypatch.setattr(lr, "LOCK_FILE", tmp_path / "live_reconciler.lock")
    monkeypatch.setattr(lr, "ensure_dirs", lambda: None)
    monkeypatch.setattr(lr, "_acquire_lock", lambda: True)
    monkeypatch.setattr(lr, "_release_lock", lambda: None)
    monkeypatch.setattr(lr, "_write_status", lambda obj: None)
    monkeypatch.setattr(lr, "get_system_guard_state", lambda **_: {"state": "RUNNING"})
    monkeypatch.setattr(lr, "live_enabled_and_armed", lambda: (True, "armed"))
    monkeypatch.setattr(lr, "_live_sandbox_enabled", lambda: True)
    monkeypatch.setattr(lr, "LiveIntentQueueSQLite", lambda: FakeQueue())
    monkeypatch.setattr(lr, "LiveTradingSQLite", lambda: FakeTrading())
    monkeypatch.setattr(lr, "LiveExchangeAdapter", FakeAdapter)

    def stop_after_one_sleep(_seconds):
        stop_file.write_text("stop\n", encoding="utf-8")

    monkeypatch.setattr(lr.time, "sleep", stop_after_one_sleep)

    lr.run_forever()

    assert upserts == []


def test_stale_not_found_does_not_upsert_order_when_queue_update_fails(monkeypatch, tmp_path):
    stop_file = tmp_path / "live_reconciler.stop"
    upserts = []

    class FakeQueue:
        def list_intents(self, *, limit=60, status):
            if status == "submit_unknown":
                return []
            return [
                {
                    "intent_id": "i1",
                    "venue": "coinbase",
                    "symbol": "BTC/USD",
                    "exchange_order_id": "ex-1",
                    "client_order_id": "cid-1",
                    "side": "buy",
                    "order_type": "limit",
                    "qty": 1.0,
                    "limit_price": 100.0,
                    "status": "submitted",
                    "updated_ts": "2020-01-01T00:00:00+00:00",
                }
            ]

        def update_status(self, *args, **kwargs):
            return False

        def get_state(self, key):
            return "0"

        def set_state(self, key, value):
            return None

    class FakeTrading:
        def upsert_order(self, row):
            upserts.append(dict(row))

        def insert_fill(self, row):
            return None

    class FakeAdapter:
        def __init__(self, venue, sandbox=False):
            pass

        def fetch_order(self, symbol, exchange_order_id):
            return None

        def fetch_my_trades(self, symbol, since_ms=None, limit=200):
            return []

        def close(self):
            return None

    monkeypatch.setenv("CBP_STALE_ORDER_MS", "1")
    monkeypatch.setattr(lr, "STOP_FILE", stop_file)
    monkeypatch.setattr(lr, "FLAGS", tmp_path)
    monkeypatch.setattr(lr, "LOCKS", tmp_path)
    monkeypatch.setattr(lr, "STATUS_FILE", tmp_path / "live_reconciler.status.json")
    monkeypatch.setattr(lr, "LOCK_FILE", tmp_path / "live_reconciler.lock")
    monkeypatch.setattr(lr, "ensure_dirs", lambda: None)
    monkeypatch.setattr(lr, "_acquire_lock", lambda: True)
    monkeypatch.setattr(lr, "_release_lock", lambda: None)
    monkeypatch.setattr(lr, "_write_status", lambda obj: None)
    monkeypatch.setattr(lr, "get_system_guard_state", lambda **_: {"state": "RUNNING"})
    monkeypatch.setattr(lr, "live_enabled_and_armed", lambda: (True, "armed"))
    monkeypatch.setattr(lr, "_live_sandbox_enabled", lambda: True)
    monkeypatch.setattr(lr, "LiveIntentQueueSQLite", lambda: FakeQueue())
    monkeypatch.setattr(lr, "LiveTradingSQLite", lambda: FakeTrading())
    monkeypatch.setattr(lr, "LiveExchangeAdapter", FakeAdapter)

    def stop_after_one_sleep(_seconds):
        stop_file.write_text("stop\n", encoding="utf-8")

    monkeypatch.setattr(lr.time, "sleep", stop_after_one_sleep)

    lr.run_forever()

    assert upserts == []


def test_stale_open_does_not_upsert_order_when_queue_update_fails(monkeypatch, tmp_path):
    stop_file = tmp_path / "live_reconciler.stop"
    upserts = []

    class FakeQueue:
        def list_intents(self, *, limit=60, status):
            if status == "submit_unknown":
                return []
            return [{
                "intent_id": "i1",
                "venue": "coinbase",
                "symbol": "BTC/USD",
                "exchange_order_id": "ex-1",
                "client_order_id": "cid-1",
                "side": "buy",
                "order_type": "limit",
                "qty": 1.0,
                "limit_price": 100.0,
                "status": "submitted",
                "updated_ts": "2020-01-01T00:00:00+00:00",
            }]

        def update_status(self, *args, **kwargs):
            return False

        def get_state(self, key):
            return "0"

        def set_state(self, key, value):
            return None

    class FakeTrading:
        def upsert_order(self, row):
            upserts.append(dict(row))

        def insert_fill(self, row):
            return None

    class FakeAdapter:
        def __init__(self, venue, sandbox=False):
            pass

        def fetch_order(self, symbol, exchange_order_id):
            return {"id": exchange_order_id, "status": "open"}

        def fetch_my_trades(self, symbol, since_ms=None, limit=200):
            return []

        def close(self):
            return None

    monkeypatch.setenv("CBP_STALE_ORDER_MS", "1")
    monkeypatch.setattr(lr, "STOP_FILE", stop_file)
    monkeypatch.setattr(lr, "FLAGS", tmp_path)
    monkeypatch.setattr(lr, "LOCKS", tmp_path)
    monkeypatch.setattr(lr, "STATUS_FILE", tmp_path / "live_reconciler.status.json")
    monkeypatch.setattr(lr, "LOCK_FILE", tmp_path / "live_reconciler.lock")
    monkeypatch.setattr(lr, "ensure_dirs", lambda: None)
    monkeypatch.setattr(lr, "_acquire_lock", lambda: True)
    monkeypatch.setattr(lr, "_release_lock", lambda: None)
    monkeypatch.setattr(lr, "_write_status", lambda obj: None)
    monkeypatch.setattr(lr, "get_system_guard_state", lambda **_: {"state": "RUNNING"})
    monkeypatch.setattr(lr, "live_enabled_and_armed", lambda: (True, "armed"))
    monkeypatch.setattr(lr, "_live_sandbox_enabled", lambda: True)
    monkeypatch.setattr(lr, "LiveIntentQueueSQLite", lambda: FakeQueue())
    monkeypatch.setattr(lr, "LiveTradingSQLite", lambda: FakeTrading())
    monkeypatch.setattr(lr, "LiveExchangeAdapter", FakeAdapter)

    def stop_after_one_sleep(_seconds):
        stop_file.write_text("stop\n", encoding="utf-8")

    monkeypatch.setattr(lr.time, "sleep", stop_after_one_sleep)

    lr.run_forever()

    assert upserts == []


def test_stale_fetch_error_does_not_upsert_order_when_queue_update_fails(monkeypatch, tmp_path):
    stop_file = tmp_path / "live_reconciler.stop"
    upserts = []

    class FakeQueue:
        def list_intents(self, *, limit=60, status):
            if status == "submit_unknown":
                return []
            return [{
                "intent_id": "i1",
                "venue": "coinbase",
                "symbol": "BTC/USD",
                "exchange_order_id": "ex-1",
                "client_order_id": "cid-1",
                "side": "buy",
                "order_type": "limit",
                "qty": 1.0,
                "limit_price": 100.0,
                "status": "submitted",
                "updated_ts": "2020-01-01T00:00:00+00:00",
            }]

        def update_status(self, *args, **kwargs):
            return False

        def get_state(self, key):
            return "0"

        def set_state(self, key, value):
            return None

    class FakeTrading:
        def upsert_order(self, row):
            upserts.append(dict(row))

        def insert_fill(self, row):
            return None

    class FakeAdapter:
        def __init__(self, venue, sandbox=False):
            pass

        def fetch_order(self, symbol, exchange_order_id):
            raise RuntimeError("network")

        def fetch_my_trades(self, symbol, since_ms=None, limit=200):
            return []

        def close(self):
            return None

    monkeypatch.setenv("CBP_STALE_ORDER_MS", "1")
    monkeypatch.setattr(lr, "STOP_FILE", stop_file)
    monkeypatch.setattr(lr, "FLAGS", tmp_path)
    monkeypatch.setattr(lr, "LOCKS", tmp_path)
    monkeypatch.setattr(lr, "STATUS_FILE", tmp_path / "live_reconciler.status.json")
    monkeypatch.setattr(lr, "LOCK_FILE", tmp_path / "live_reconciler.lock")
    monkeypatch.setattr(lr, "ensure_dirs", lambda: None)
    monkeypatch.setattr(lr, "_acquire_lock", lambda: True)
    monkeypatch.setattr(lr, "_release_lock", lambda: None)
    monkeypatch.setattr(lr, "_write_status", lambda obj: None)
    monkeypatch.setattr(lr, "get_system_guard_state", lambda **_: {"state": "RUNNING"})
    monkeypatch.setattr(lr, "live_enabled_and_armed", lambda: (True, "armed"))
    monkeypatch.setattr(lr, "_live_sandbox_enabled", lambda: True)
    monkeypatch.setattr(lr, "LiveIntentQueueSQLite", lambda: FakeQueue())
    monkeypatch.setattr(lr, "LiveTradingSQLite", lambda: FakeTrading())
    monkeypatch.setattr(lr, "LiveExchangeAdapter", FakeAdapter)

    def stop_after_one_sleep(_seconds):
        stop_file.write_text("stop\n", encoding="utf-8")

    monkeypatch.setattr(lr.time, "sleep", stop_after_one_sleep)

    lr.run_forever()

    assert upserts == []
