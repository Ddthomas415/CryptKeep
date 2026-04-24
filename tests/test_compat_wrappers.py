from pathlib import Path
import importlib

def test_marketdata_compat_python_modules_retired():
    retired = [
        "services/marketdata/__init__.py",
        "services/marketdata/mark_cache.py",
        "services/marketdata/ohlcv_fetcher.py",
        "services/marketdata/ws_clients.py",
        "services/marketdata/ws_feature_blacklist.py",
        "services/marketdata/ws_ticker_feed.py",
    ]
    for p in retired:
        assert not Path(p).exists(), p

def test_marketdata_canonical_replacement_importable():
    mod = importlib.import_module("services.market_data.ws_feature_blacklist")
    assert mod is not None
    assert hasattr(mod, "__file__")
