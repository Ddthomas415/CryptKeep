from pathlib import Path

def test_signals_webhook_requires_hmac() -> None:
    text = Path("services/signals/webhook_server.py").read_text()
    assert "SIGNAL_WEBHOOK_SECRET" in text
    assert "_validate_hmac" in text
    assert '"reason": "unauthorized"' in text
