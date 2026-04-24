from services.execution import intent_reconciler as mod

def test_reconciler_journals_fills_before_marking_filled(monkeypatch):
    calls = []

    class FakeQDB:
        def list_intents(self, limit=50, status="submitted"):
            return [{
                "intent_id": "i1",
                "linked_order_id": "o1",
                "symbol": "BTC/USDT",
                "side": "buy",
                "exchange": "paper",
                "venue": "paper",
                "client_order_id": "coid-1",
                "meta": {},
            }]

        def update_status(self, intent_id, status, linked_order_id=None, **_kwargs):
            calls.append(("update_status", intent_id, status, linked_order_id))

    class FakePDB:
        def get_order_by_order_id(self, order_id):
            return {
                "order_id": order_id,
                "status": "filled",
                "symbol": "BTC/USDT",
                "venue": "paper",
                "side": "buy",
            }

        def list_fills_for_order(self, order_id, limit=5000):
            return [{
                "fill_id": "f1",
                "symbol": "BTC/USDT",
                "side": "buy",
                "qty": 1.0,
                "price": 100.0,
                "fee": 0.1,
                "fee_currency": "USDT",
                "ts": "t1",
            }]

        def get_position(self, symbol):
            return {"qty": None, "avg_price": None}

        def get_state(self, key):
            return "0.0"

    class FakeJDB:
        def insert_fill(self, journal_row):
            calls.append(("insert_fill", journal_row["fill_id"], journal_row["order_id"]))

        def count(self):
            return 1

    monkeypatch.setattr(mod, "IntentQueueSQLite", lambda *_a, **_k: FakeQDB())
    monkeypatch.setattr(mod, "PaperTradingSQLite", lambda *_a, **_k: FakePDB())
    monkeypatch.setattr(mod, "TradeJournalSQLite", lambda *_a, **_k: FakeJDB())
    monkeypatch.setattr(mod, "log_strategy_outcome", lambda *_a, **_k: None)

    out = mod.reconcile_once()

    assert out is not None
    assert calls == [
        ("insert_fill", "f1", "o1"),
        ("update_status", "i1", "filled", "o1"),
    ]
