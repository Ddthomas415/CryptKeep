from pathlib import Path

def test_crypto_edge_scripts_redact_store_path() -> None:
    paths = [
        "scripts/record_crypto_edge_snapshot.py",
        "scripts/collect_live_crypto_edge_snapshot.py",
        "scripts/load_sample_crypto_edge_data.py",
    ]
    for path in paths:
        text = Path(path).read_text()
        assert 'str(store.path)' not in text, path
        assert '"store_path": "redacted"' in text or 'store_path": "redacted"' in text or 'store_path": "redacted"' in text
