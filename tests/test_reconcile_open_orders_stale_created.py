from services.execution import _executor_reconcile as er


def test_reconcile_open_orders_leaves_unmatched_created_dedupe_row(monkeypatch, tmp_path):
    calls = {"mark_error": 0, "mark_submitted": 0, "set_remote": 0}

    class FakeStore:
        def list_needs_reconcile(self, *, exchange_id, limit=200):
            return [{
                "exchange_id": exchange_id,
                "intent_id": "intent-1",
                "symbol": "BTC/USD",
                "client_order_id": "cid-1",
                "remote_order_id": None,
                "status": "created",
                "created_ts_ms": 0,
                "updated_ts_ms": 0,
            }]

        def set_remote_id_if_empty(self, **kwargs):
            calls["set_remote"] += 1

        def mark_submitted(self, **kwargs):
            calls["mark_submitted"] += 1

        def mark_error(self, **kwargs):
            calls["mark_error"] += 1

    class FakeClient:
        def __init__(self, exchange_id, sandbox=False):
            self.exchange_id = exchange_id
            self.sandbox = sandbox

    monkeypatch.setattr(er, "OrderDedupeStore", lambda exec_db: FakeStore())
    monkeypatch.setattr(er, "ExchangeClient", FakeClient)
    monkeypatch.setattr(er, "_open_reconcile_session", lambda client: (object(), True))
    monkeypatch.setattr(er, "_close_reconcile_session", lambda session, owned: None)
    monkeypatch.setattr(er, "_fetch_open_orders_for_reconcile", lambda *args, **kwargs: [])
    monkeypatch.setattr(er, "_record_execution_metric", lambda **kwargs: None)

    out = er.reconcile_open_orders(str(tmp_path / "execution.sqlite"), "coinbase", limit=10)

    assert out == {"ok": True, "rows": 1, "matched_open": 0}
    assert calls["set_remote"] == 0
    assert calls["mark_submitted"] == 0

    # Current gap proof: unmatched created rows are not transitioned anywhere.
    assert calls["mark_error"] == 1


def test_reconcile_open_orders_leaves_fresh_unmatched_created_dedupe_row_pending(monkeypatch, tmp_path):
    calls = {"mark_error": 0, "mark_submitted": 0, "set_remote": 0}

    class FakeStore:
        def list_needs_reconcile(self, *, exchange_id, limit=200):
            import time
            now_ms = int(time.time() * 1000)
            return [{
                "exchange_id": exchange_id,
                "intent_id": "intent-1",
                "symbol": "BTC/USD",
                "client_order_id": "cid-1",
                "remote_order_id": None,
                "status": "created",
                "created_ts_ms": now_ms,
                "updated_ts_ms": now_ms,
            }]

        def set_remote_id_if_empty(self, **kwargs):
            calls["set_remote"] += 1

        def mark_submitted(self, **kwargs):
            calls["mark_submitted"] += 1

        def mark_error(self, **kwargs):
            calls["mark_error"] += 1

    class FakeClient:
        def __init__(self, exchange_id, sandbox=False):
            self.exchange_id = exchange_id
            self.sandbox = sandbox

    monkeypatch.setattr(er, "OrderDedupeStore", lambda exec_db: FakeStore())
    monkeypatch.setattr(er, "ExchangeClient", FakeClient)
    monkeypatch.setattr(er, "_open_reconcile_session", lambda client: (object(), True))
    monkeypatch.setattr(er, "_close_reconcile_session", lambda session, owned: None)
    monkeypatch.setattr(er, "_fetch_open_orders_for_reconcile", lambda *args, **kwargs: [])
    monkeypatch.setattr(er, "_record_execution_metric", lambda **kwargs: None)

    out = er.reconcile_open_orders(str(tmp_path / "execution.sqlite"), "coinbase", limit=10)

    assert out == {"ok": True, "rows": 1, "matched_open": 0}
    assert calls["set_remote"] == 0
    assert calls["mark_submitted"] == 0
    assert calls["mark_error"] == 0
