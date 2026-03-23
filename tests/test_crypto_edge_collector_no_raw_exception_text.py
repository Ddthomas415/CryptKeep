from pathlib import Path

def test_crypto_edge_collector_does_not_log_raw_exception_text() -> None:
    text = Path("services/analytics/crypto_edge_collector_service.py").read_text()
    assert '"error": str(exc)' not in text
    assert '"error_type": type(exc).__name__' in text
