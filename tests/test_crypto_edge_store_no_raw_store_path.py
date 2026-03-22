from pathlib import Path

def test_crypto_edge_store_does_not_expose_raw_store_path() -> None:
    text = Path("storage/crypto_edge_store_sqlite.py").read_text()
    assert 'report["store_path"] = str(self.path)' not in text
