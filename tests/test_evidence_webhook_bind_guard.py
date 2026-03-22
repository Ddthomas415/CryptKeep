import pytest
from services.evidence import webhook_server as mod

def test_evidence_webhook_rejects_public_bind() -> None:
    with pytest.raises(RuntimeError):
        mod._bind_guard({"host": "0.0.0.0"})
