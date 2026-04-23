from unittest.mock import patch

import services.execution.intent_store as store


def test_claim_next_ready_race_winner_takes_all(monkeypatch):
    """Explicitly simulate same-row SELECT race and UPDATE rowcount winner/loser."""
    selected = [
        ("test::BTC::BUY::1m::1730000000000",),
        ("test::BTC::BUY::1m::1730000000000",),
    ]
    rowcounts = [1, 0]

    class FakeCursor:
        def __init__(self):
            self.rowcount = -1

        def execute(self, sql, params=None):
            if sql.startswith("UPDATE intents SET status='SENDING'"):
                self.rowcount = rowcounts.pop(0)
            return None

        def fetchone(self):
            return selected.pop(0) if selected else None

    class FakeCon:
        def cursor(self):
            return FakeCursor()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(store, "_connect", lambda: FakeCon())
    monkeypatch.setattr(
        store,
        "get_intent",
        lambda intent_id: {"intent_id": intent_id, "status": "SENDING"},
    )

    winner = store.claim_next_ready()
    loser = store.claim_next_ready()

    assert winner == {
        "intent_id": "test::BTC::BUY::1m::1730000000000",
        "status": "SENDING",
    }
    assert loser is None
