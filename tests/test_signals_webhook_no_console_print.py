from pathlib import Path

def test_signals_webhook_has_no_console_print() -> None:
    text = Path("services/signals/webhook_server.py").read_text()
    assert 'print({"ok": True, "listening":' not in text
