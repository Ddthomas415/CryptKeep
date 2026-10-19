"""Copy into the isolated candidate tests directory; never run against live state."""
from tests.test_live_executor_intent_ttl import rig, _add, _status
from services.execution import live_executor as le


def test_remote_order_evidence_survives_a_market_quality_block(rig, monkeypatch):
    cfg, store, client = rig
    _add(store, "sent-blocked", 3600, reason="remote_id=ord-77")
    monkeypatch.setattr(le, "check_market_quality", lambda *_a, **_k: (False, "stale"))
    first = le.submit_pending_live(cfg)
    assert first["expired"] == 0
    second = le.submit_pending_live(cfg)
    assert second["expired"] == 0, "remote order must not be locally expired"
    assert _status(store, "sent-blocked")[0] != "canceled"
    assert client.calls == []
