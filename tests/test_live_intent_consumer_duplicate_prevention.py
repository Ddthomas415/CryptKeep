from services.execution import live_intent_consumer as lic


def test_restart_after_submit_before_status_update_does_not_submit_duplicate(monkeypatch, tmp_path):
    submit_calls = []
    dedupe_rows = {}

    class FakeDedupe:
        def claim(self, *, exchange_id, intent_id, symbol, client_order_id, meta=None):
            key = (exchange_id, intent_id)
            row = dedupe_rows.get(key)
            if row is None:
                row = {
                    "exchange_id": exchange_id,
                    "intent_id": intent_id,
                    "symbol": symbol,
                    "client_order_id": client_order_id,
                    "remote_order_id": None,
                    "status": "created",
                }
                dedupe_rows[key] = row
                out = dict(row)
                out["_inserted"] = True
                return out

            if row["status"] in {"created", "submitted", "unknown"}:
                raise SystemExit("dedupe_blocked_restart_submit")
            out = dict(row)
            out["_inserted"] = False
            return out

        def mark_submitted(self, **kwargs):
            dedupe_rows[(kwargs["exchange_id"], kwargs["intent_id"])]["status"] = "submitted"
            dedupe_rows[(kwargs["exchange_id"], kwargs["intent_id"])]["remote_order_id"] = kwargs.get("remote_order_id")

        def mark_unknown(self, **kwargs):
            dedupe_rows[(kwargs["exchange_id"], kwargs["intent_id"])]["status"] = "unknown"

    class FakeQueue:
        def __init__(self):
            self.claimed = False

        def claim_next_queued(self, limit=10):
            if self.claimed:
                raise SystemExit("queue_exhausted")
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
            return True

        def get_state(self, key):
            return "2026-01-01"

        def reset_risk_state_for_day(self, day):
            return None

        def atomic_risk_claim(self, **kwargs):
            return True, None

    class FakeTrading:
        def upsert_order(self, row):
            return None

    class FakeAdapter:
        def __init__(self, venue, sandbox=False):
            pass

        def find_order_by_client_oid(self, symbol, client_order_id):
            return None

        def submit_order(self, **kwargs):
            submit_calls.append(dict(kwargs))
            raise SystemExit("crash_after_exchange_submit_before_local_persist")

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

    def setup_common():
        monkeypatch.setattr(lic, "STOP_FILE", tmp_path / "live_intent_consumer.stop")
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
        monkeypatch.setattr(lic, "OrderDedupeStore", lambda: FakeDedupe())

    setup_common()
    try:
        lic.run_forever()
    except SystemExit as exc:
        assert str(exc) == "crash_after_exchange_submit_before_local_persist"

    assert len(submit_calls) == 1
    assert dedupe_rows[("coinbase", "i1")]["status"] == "created"
    assert dedupe_rows[("coinbase", "i1")]["remote_order_id"] is None

    setup_common()
    try:
        lic.run_forever()
    except SystemExit as exc:
        assert str(exc) == "dedupe_blocked_restart_submit"

    assert len(submit_calls) == 1
