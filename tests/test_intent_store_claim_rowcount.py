from services.execution import intent_store as mod

def test_claim_next_ready_returns_none_when_update_does_not_claim(monkeypatch):
    class FakeCursor:
        def __init__(self, row=None, rowcount=0):
            self._row = row
            self.rowcount = rowcount
        def execute(self, *_a, **_k):
            return self
        def fetchone(self):
            return self._row

    class FakeConn:
        def __init__(self):
            self.select_cursor = FakeCursor(row=("intent-1",))
            self.update_cursor = FakeCursor(row=None, rowcount=0)
            self.calls = []
        def cursor(self):
            return self.select_cursor
        def execute(self, sql, params):
            self.calls.append((sql, params))
            return self.update_cursor
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False
        def close(self):
            pass

    fake = FakeConn()

    monkeypatch.setattr(mod, "_connect", lambda: fake)
    monkeypatch.setattr(mod, "get_intent", lambda intent_id: {"intent_id": intent_id, "status": "SENDING"})

    out = mod.claim_next_ready()

    assert out is None
