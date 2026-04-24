from pathlib import Path
import importlib

def test_service_storage_python_modules_retired():
    retired = [
        "services/storage/__init__.py",
        "services/storage/paper_trading_sqlite.py",
        "services/storage/trade_journal_sqlite.py",
    ]
    for p in retired:
        assert not Path(p).exists(), p

def test_storage_canonical_replacement_importable():
    mod = importlib.import_module("storage.paper_trading_sqlite")
    assert mod is not None
    assert hasattr(mod, "__file__")

def test_trade_journal_storage_canonical_replacement_importable():
    mod = importlib.import_module("storage.trade_journal_sqlite")
    assert mod is not None
    assert hasattr(mod, "__file__")
