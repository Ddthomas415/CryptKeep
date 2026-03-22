from services.evidence import webhook_server as mod

def test_evidence_webhook_requires_hmac_by_default(monkeypatch):
    monkeypatch.setattr(mod, "load_user_yaml", lambda: {})
    cfg = mod._cfg()
    assert cfg["require_hmac"] is True
