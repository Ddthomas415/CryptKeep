from pathlib import Path

def test_crypto_edge_collector_status_redacts_store_path() -> None:
    text = Path("services/analytics/crypto_edge_collector_service.py").read_text()
    assert 'out["store_path"] = str(store.path)' not in text
    assert 'out["store_path"] = "redacted"' in text
