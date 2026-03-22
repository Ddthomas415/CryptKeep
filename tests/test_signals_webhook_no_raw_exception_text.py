from pathlib import Path

def test_signals_webhook_does_not_return_raw_exception_text() -> None:
    text = Path("services/signals/webhook_server.py").read_text()
    assert 'f"{type(e).__name__}:{e}"' not in text
    assert '"error_type": type(e).__name__' in text
