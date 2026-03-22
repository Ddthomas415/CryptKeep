import pytest
from services.signals import webhook_server as mod

def test_signals_webhook_rejects_public_bind() -> None:
    with pytest.raises(RuntimeError):
        mod.run(host="0.0.0.0", port=8787)
