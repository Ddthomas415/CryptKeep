from __future__ import annotations

import importlib

from services.exchanges import symbols as exchange_symbols
from services.market_data import symbol_normalize


def test_symbol_normalize_wrapper_normalizes_single_and_batch_symbols():
    assert symbol_normalize.normalize_symbol("btc-usd") == "BTC/USD"
    assert symbol_normalize.normalize_symbol("eth_usdt") == "ETH/USDT"
    batch = symbol_normalize.normalize_symbols(["btc-usd", "ETH_USDT", "btc-usd"])
    assert batch == {
        "normalized": ["BTC/USD", "ETH/USDT"],
        "invalid": [],
        "count": 2,
    }


def test_exchange_symbols_wrapper_exposes_normalize_symbol():
    assert exchange_symbols.normalize_symbol("btc-usd") == "BTC/USD"
    assert exchange_symbols.coinbase_native("btc/usd") == "BTC-USD"


def test_stale_import_modules_now_import_cleanly():
    importlib.import_module("services.admin.position_reconcile")
    importlib.import_module("services.diagnostics.ui_live_gate")
    importlib.import_module("services.marketdata.ws_feature_blacklist")
    importlib.import_module("services.evidence.ingest")
