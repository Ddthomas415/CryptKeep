from services.execution import live_reconciler as lr


def test_same_symbol_trades_are_not_cross_attributed_between_orders(monkeypatch, tmp_path):
    fills = []
    sink_fills = []

    class FakeQueue:
        def __init__(self):
            self.state = {}
            self.calls = 0

        def list_intents(self, *, limit=60, status):
            if status == "submit_unknown":
                return []
            if status != "submitted":
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
                },
                {
                    "intent_id": "i2",
                    "venue": "coinbase",
                    "symbol": "BTC/USD",
                    "exchange_order_id": "ex-2",
                    "client_order_id": "cid-2",
                    "side": "buy",
                    "order_type": "limit",
                    "qty": 1.0,
                    "limit_price": 200.0,
                    "status": "submitted",
                    "updated_ts": "2026-01-01T00:00:00+00:00",
                },
            ]

        def update_status(self, *args, **kwargs):
            return True

        def get_state(self, key):
            return self.state.get(key, "0")

        def set_state(self, key, value):
            self.state[key] = value

    class FakeTrading:
        def upsert_order(self, row):
            return None

        def insert_fill(self, row):
            fills.append(dict(row))

    class FakeAdapter:
        def __init__(self, venue, sandbox=False):
            pass

        def fetch_order(self, symbol, exchange_order_id):
            return {"id": exchange_order_id, "status": "open"}

        def fetch_my_trades(self, symbol, since_ms=None, limit=200):
            return [
                {
                    "id": "trade-1",
                    "order": "ex-1",
                    "timestamp": 1000,
                    "datetime": "2026-01-01T00:00:01Z",
                    "side": "buy",
                    "amount": 1.0,
                    "price": 100.0,
                    "fee": {"cost": 0.1, "currency": "USD"},
                }
            ]

        def close(self):
            return None

    stop_file = tmp_path / "live_reconciler.stop"

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
    monkeypatch.setattr(lr, "_default_exec_db_path", lambda: str(tmp_path / "execution.sqlite"))
    monkeypatch.setattr(
        lr,
        "_emit_canonical_fill",
        lambda *, exec_db, fill: sink_fills.append({"exec_db": exec_db, "fill": dict(fill)}),
    )

    def stop_after_one_sleep(_seconds):
        stop_file.write_text("stop\n", encoding="utf-8")

    monkeypatch.setattr(lr.time, "sleep", stop_after_one_sleep)

    lr.run_forever()

    assert fills
    assert all(f["exchange_order_id"] == "ex-1" for f in fills)
    assert not any(f["exchange_order_id"] == "ex-2" for f in fills)
    assert len(sink_fills) == 1
    assert sink_fills[0]["exec_db"] == str(tmp_path / "execution.sqlite")
    assert sink_fills[0]["fill"]["fill_id"] == "trade-1"
    assert sink_fills[0]["fill"]["fee_usd"] == 0.1
    assert sink_fills[0]["fill"]["order_id"] == "ex-1"
