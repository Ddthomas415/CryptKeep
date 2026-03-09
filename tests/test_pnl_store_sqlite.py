from __future__ import annotations

import asyncio
import importlib



def _reload_pnl_modules():
    import services.os.app_paths as app_paths
    import storage.pnl_store_sqlite as pnl_store

    importlib.reload(app_paths)
    importlib.reload(pnl_store)
    return pnl_store



def test_last_fills_uses_real_schema_and_returns_latest_first(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    pnl_store = _reload_pnl_modules()

    store = pnl_store.PnLStoreSQLite()
    asyncio.run(store.record_fill("coinbase", "BTC/USD", "buy", 1.0, 100.0, fee=0.25, fee_ccy="USD"))
    asyncio.run(store.record_fill("coinbase", "ETH/USD", "sell", 2.0, 50.0, fee=0.10, fee_ccy="USD"))

    fills = store.last_fills(limit=10)

    assert len(fills) == 2
    assert fills[0]["symbol"] == "ETH/USD"
    assert fills[1]["symbol"] == "BTC/USD"
    assert fills[0]["id"] > fills[1]["id"]
    assert fills[0]["ext_id"] is None
    assert fills[0]["fee_ccy"] == "USD"



def test_last_fills_empty_db_returns_empty_list(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    pnl_store = _reload_pnl_modules()

    store = pnl_store.PnLStoreSQLite()

    assert store.last_fills(limit=5) == []
