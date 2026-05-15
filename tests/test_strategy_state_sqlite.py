from __future__ import annotations

import importlib


def _reload_strategy_state(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    import services.os.app_paths as app_paths
    import storage.strategy_state_sqlite as strategy_state_sqlite

    importlib.reload(app_paths)
    importlib.reload(strategy_state_sqlite)
    return strategy_state_sqlite


def test_strategy_state_delete_removes_existing_key(monkeypatch, tmp_path) -> None:
    mod = _reload_strategy_state(monkeypatch, tmp_path)
    store = mod.StrategyStateSQLite()

    store.set("warmed:coinbase:BTC/USDT:sma_200_trend", "1")
    assert store.get("warmed:coinbase:BTC/USDT:sma_200_trend") == "1"

    store.delete("warmed:coinbase:BTC/USDT:sma_200_trend")

    assert store.get("warmed:coinbase:BTC/USDT:sma_200_trend") is None


def test_strategy_state_delete_missing_key_is_safe(monkeypatch, tmp_path) -> None:
    mod = _reload_strategy_state(monkeypatch, tmp_path)
    store = mod.StrategyStateSQLite()

    store.delete("missing:key")

    assert store.get("missing:key") is None
