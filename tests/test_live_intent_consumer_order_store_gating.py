from services.execution import live_intent_consumer as lic


def test_recovered_before_submit_does_not_upsert_order_when_queue_update_fails(monkeypatch, tmp_path):
    stop_file = tmp_path / "live_intent_consumer.stop"
    upserts = []

    class FakeQueue:
        def __init__(self):
            self.claimed = False

        def claim_next_queued(self, limit=10):
            if self.claimed:
                return []
            self.claimed = True
            return [{
                "intent_id": "i1",
                "venue": "coinbase",
                "symbol": "BTC/USD",
                "side": "buy",
                "order_type": "limit",
                "qty": 1.0,
                "limit_price": 100.0,
                "client_order_id": "cid-1",
                "status": "queued",
                "meta": {},
            }]

        def update_status(self, *args, **kwargs):
            return False

        def get_state(self, key):
            return "2026-01-01"

        def reset_risk_state_for_day(self, day):
            return None

        def atomic_risk_claim(self, **kwargs):
            return True, None

    class FakeTrading:
        def upsert_order(self, row):
            upserts.append(dict(row))

    class FakeAdapter:
        def __init__(self, venue, sandbox=False):
            pass

        def find_order_by_client_oid(self, symbol, client_order_id):
            return {"id": "ex-1"}

        def close(self):
            return None

    class FakeDecision:
        allowed = True
        side = "buy"
        order_type = "limit"
        qty = 1.0
        limit_price = 100.0
        reason = "ok"

    monkeypatch.setattr(lic, "STOP_FILE", stop_file)
    monkeypatch.setattr(lic, "FLAGS", tmp_path)
    monkeypatch.setattr(lic, "LOCKS", tmp_path)
    monkeypatch.setattr(lic, "STATUS_FILE", tmp_path / "live_intent_consumer.status.json")
    monkeypatch.setattr(lic, "LOCK_FILE", tmp_path / "live_intent_consumer.lock")
    monkeypatch.setattr(lic, "ensure_dirs", lambda: None)
    monkeypatch.setattr(lic, "_acquire_lock", lambda: True)
    monkeypatch.setattr(lic, "_release_lock", lambda: None)
    monkeypatch.setattr(lic, "_write_status", lambda obj: None)
    monkeypatch.setattr(lic, "live_enabled_and_armed", lambda: (True, "armed"))
    monkeypatch.setattr(lic, "is_snapshot_fresh", lambda: (True, "fresh"))
    monkeypatch.setattr(lic, "_live_sandbox_enabled", lambda: True)
    monkeypatch.setattr(lic, "mq_check", lambda venue, symbol: {"ok": True, "last": 100.0})
    async def fake_decide_order(**kwargs):
        return FakeDecision()

    monkeypatch.setattr(lic, "decide_order", fake_decide_order)
    monkeypatch.setattr(lic, "LiveIntentQueueSQLite", lambda: FakeQueue())
    monkeypatch.setattr(lic, "LiveTradingSQLite", lambda: FakeTrading())
    monkeypatch.setattr(lic, "LiveExchangeAdapter", FakeAdapter)

    def stop_after_one_sleep(_seconds):
        stop_file.write_text("stop\n", encoding="utf-8")

    monkeypatch.setattr(lic.time, "sleep", stop_after_one_sleep)

    lic.run_forever()

    assert upserts == []


def test_submit_success_does_not_upsert_order_when_queue_update_fails(monkeypatch, tmp_path):
    stop_file = tmp_path / "live_intent_consumer.stop"
    upserts = []

    class FakeQueue:
        def __init__(self):
            self.claimed = False

        def claim_next_queued(self, limit=10):
            if self.claimed:
                return []
            self.claimed = True
            return [{
                "intent_id": "i1",
                "venue": "coinbase",
                "symbol": "BTC/USD",
                "side": "buy",
                "order_type": "limit",
                "qty": 1.0,
                "limit_price": 100.0,
                "client_order_id": "cid-1",
                "status": "queued",
                "meta": {},
            }]

        def update_status(self, *args, **kwargs):
            return False

        def get_state(self, key):
            return "2026-01-01"

        def reset_risk_state_for_day(self, day):
            return None

        def atomic_risk_claim(self, **kwargs):
            return True, None

    class FakeTrading:
        def upsert_order(self, row):
            upserts.append(dict(row))

    class FakeAdapter:
        def __init__(self, venue, sandbox=False):
            pass

        def find_order_by_client_oid(self, symbol, client_order_id):
            return None

        def submit_order(self, **kwargs):
            return {"id": "ex-1"}

        def close(self):
            return None

    class FakeDecision:
        allowed = True
        side = "buy"
        order_type = "limit"
        qty = 1.0
        limit_price = 100.0
        reason = "ok"

    async def fake_decide_order(**kwargs):
        return FakeDecision()

    monkeypatch.setattr(lic, "STOP_FILE", stop_file)
    monkeypatch.setattr(lic, "FLAGS", tmp_path)
    monkeypatch.setattr(lic, "LOCKS", tmp_path)
    monkeypatch.setattr(lic, "STATUS_FILE", tmp_path / "live_intent_consumer.status.json")
    monkeypatch.setattr(lic, "LOCK_FILE", tmp_path / "live_intent_consumer.lock")
    monkeypatch.setattr(lic, "ensure_dirs", lambda: None)
    monkeypatch.setattr(lic, "_acquire_lock", lambda: True)
    monkeypatch.setattr(lic, "_release_lock", lambda: None)
    monkeypatch.setattr(lic, "_write_status", lambda obj: None)
    monkeypatch.setattr(lic, "live_enabled_and_armed", lambda: (True, "armed"))
    monkeypatch.setattr(lic, "is_snapshot_fresh", lambda: (True, "fresh"))
    monkeypatch.setattr(lic, "_live_sandbox_enabled", lambda: True)
    monkeypatch.setattr(lic, "mq_check", lambda venue, symbol: {"ok": True, "last": 100.0})
    monkeypatch.setattr(lic, "decide_order", fake_decide_order)
    monkeypatch.setattr(lic, "LiveIntentQueueSQLite", lambda: FakeQueue())
    monkeypatch.setattr(lic, "LiveTradingSQLite", lambda: FakeTrading())
    monkeypatch.setattr(lic, "LiveExchangeAdapter", FakeAdapter)

    def stop_after_one_sleep(_seconds):
        stop_file.write_text("stop\n", encoding="utf-8")

    monkeypatch.setattr(lic.time, "sleep", stop_after_one_sleep)

    lic.run_forever()

    assert upserts == []


def test_missing_exchange_order_id_does_not_upsert_order_when_queue_update_fails(monkeypatch, tmp_path):
    stop_file = tmp_path / "live_intent_consumer.stop"
    upserts = []

    class FakeQueue:
        def __init__(self):
            self.claimed = False

        def claim_next_queued(self, limit=10):
            if self.claimed:
                return []
            self.claimed = True
            return [{
                "intent_id": "i1",
                "venue": "coinbase",
                "symbol": "BTC/USD",
                "side": "buy",
                "order_type": "limit",
                "qty": 1.0,
                "limit_price": 100.0,
                "client_order_id": "cid-1",
                "status": "queued",
                "meta": {},
            }]

        def update_status(self, *args, **kwargs):
            return False

        def get_state(self, key):
            return "2026-01-01"

        def reset_risk_state_for_day(self, day):
            return None

        def atomic_risk_claim(self, **kwargs):
            return True, None

    class FakeTrading:
        def upsert_order(self, row):
            upserts.append(dict(row))

    class FakeAdapter:
        def __init__(self, venue, sandbox=False):
            pass

        def find_order_by_client_oid(self, symbol, client_order_id):
            return None

        def submit_order(self, **kwargs):
            return {}

        def close(self):
            return None

    class FakeDecision:
        allowed = True
        side = "buy"
        order_type = "limit"
        qty = 1.0
        limit_price = 100.0
        reason = "ok"

    async def fake_decide_order(**kwargs):
        return FakeDecision()

    monkeypatch.setattr(lic, "STOP_FILE", stop_file)
    monkeypatch.setattr(lic, "FLAGS", tmp_path)
    monkeypatch.setattr(lic, "LOCKS", tmp_path)
    monkeypatch.setattr(lic, "STATUS_FILE", tmp_path / "live_intent_consumer.status.json")
    monkeypatch.setattr(lic, "LOCK_FILE", tmp_path / "live_intent_consumer.lock")
    monkeypatch.setattr(lic, "ensure_dirs", lambda: None)
    monkeypatch.setattr(lic, "_acquire_lock", lambda: True)
    monkeypatch.setattr(lic, "_release_lock", lambda: None)
    monkeypatch.setattr(lic, "_write_status", lambda obj: None)
    monkeypatch.setattr(lic, "live_enabled_and_armed", lambda: (True, "armed"))
    monkeypatch.setattr(lic, "is_snapshot_fresh", lambda: (True, "fresh"))
    monkeypatch.setattr(lic, "_live_sandbox_enabled", lambda: True)
    monkeypatch.setattr(lic, "mq_check", lambda venue, symbol: {"ok": True, "last": 100.0})
    monkeypatch.setattr(lic, "decide_order", fake_decide_order)
    monkeypatch.setattr(lic, "LiveIntentQueueSQLite", lambda: FakeQueue())
    monkeypatch.setattr(lic, "LiveTradingSQLite", lambda: FakeTrading())
    monkeypatch.setattr(lic, "LiveExchangeAdapter", FakeAdapter)

    def stop_after_one_sleep(_seconds):
        stop_file.write_text("stop\n", encoding="utf-8")

    monkeypatch.setattr(lic.time, "sleep", stop_after_one_sleep)

    lic.run_forever()

    assert upserts == []


def test_exception_submit_unknown_does_not_upsert_order_when_queue_update_fails(monkeypatch, tmp_path):
    stop_file = tmp_path / "live_intent_consumer.stop"
    upserts = []

    class FakeQueue:
        def __init__(self):
            self.claimed = False

        def claim_next_queued(self, limit=10):
            if self.claimed:
                return []
            self.claimed = True
            return [{
                "intent_id": "i1",
                "venue": "coinbase",
                "symbol": "BTC/USD",
                "side": "buy",
                "order_type": "limit",
                "qty": 1.0,
                "limit_price": 100.0,
                "client_order_id": "cid-1",
                "status": "queued",
                "meta": {},
            }]

        def update_status(self, *args, **kwargs):
            return False

        def get_state(self, key):
            return "2026-01-01"

        def reset_risk_state_for_day(self, day):
            return None

        def atomic_risk_claim(self, **kwargs):
            return True, None

    class FakeTrading:
        def upsert_order(self, row):
            upserts.append(dict(row))

    class FakeAdapter:
        def __init__(self, venue, sandbox=False):
            pass

        def find_order_by_client_oid(self, symbol, client_order_id):
            return None

        def submit_order(self, **kwargs):
            raise RuntimeError("submit failed")

        def close(self):
            return None

    class FakeDecision:
        allowed = True
        side = "buy"
        order_type = "limit"
        qty = 1.0
        limit_price = 100.0
        reason = "ok"

    async def fake_decide_order(**kwargs):
        return FakeDecision()

    monkeypatch.setattr(lic, "STOP_FILE", stop_file)
    monkeypatch.setattr(lic, "FLAGS", tmp_path)
    monkeypatch.setattr(lic, "LOCKS", tmp_path)
    monkeypatch.setattr(lic, "STATUS_FILE", tmp_path / "live_intent_consumer.status.json")
    monkeypatch.setattr(lic, "LOCK_FILE", tmp_path / "live_intent_consumer.lock")
    monkeypatch.setattr(lic, "ensure_dirs", lambda: None)
    monkeypatch.setattr(lic, "_acquire_lock", lambda: True)
    monkeypatch.setattr(lic, "_release_lock", lambda: None)
    monkeypatch.setattr(lic, "_write_status", lambda obj: None)
    monkeypatch.setattr(lic, "live_enabled_and_armed", lambda: (True, "armed"))
    monkeypatch.setattr(lic, "is_snapshot_fresh", lambda: (True, "fresh"))
    monkeypatch.setattr(lic, "_live_sandbox_enabled", lambda: True)
    monkeypatch.setattr(lic, "mq_check", lambda venue, symbol: {"ok": True, "last": 100.0})
    monkeypatch.setattr(lic, "decide_order", fake_decide_order)
    monkeypatch.setattr(lic, "LiveIntentQueueSQLite", lambda: FakeQueue())
    monkeypatch.setattr(lic, "LiveTradingSQLite", lambda: FakeTrading())
    monkeypatch.setattr(lic, "LiveExchangeAdapter", FakeAdapter)

    def stop_after_one_sleep(_seconds):
        stop_file.write_text("stop\n", encoding="utf-8")

    monkeypatch.setattr(lic.time, "sleep", stop_after_one_sleep)

    lic.run_forever()

    assert upserts == []
