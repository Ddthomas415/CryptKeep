import storage.live_intent_queue_sqlite as mod


def test_reset_risk_state_for_day_updates_reserved_keys_atomically(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "DB_PATH", tmp_path / "live_intent_queue.sqlite")
    db = mod.LiveIntentQueueSQLite()

    db.reset_risk_state_for_day("2026-04-26")

    assert db.get_state("risk:day") == "2026-04-26"
    assert db.get_state("risk:trades") == "0"
    assert db.get_state("risk:notional") == "0.0"


def test_non_reserved_state_keys_still_use_generic_set_state(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "DB_PATH", tmp_path / "live_intent_queue.sqlite")
    db = mod.LiveIntentQueueSQLite()

    db.set_state("trades_since_ms:coinbase:BTC/USD", "123")

    assert db.get_state("trades_since_ms:coinbase:BTC/USD") == "123"


def test_reserved_risk_keys_are_not_writable_through_generic_set_state(tmp_path, monkeypatch):
    import pytest

    monkeypatch.setattr(mod, "DB_PATH", tmp_path / "live_intent_queue.sqlite")
    db = mod.LiveIntentQueueSQLite()

    for key in ("risk:day", "risk:trades", "risk:notional"):
        with pytest.raises(ValueError, match="reserved live risk state key"):
            db.set_state(key, "bad")
