from __future__ import annotations

import importlib
import json

import pytest


def _reload_intent_executor(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path / "state"))
    import services.os.app_paths as app_paths
    import scripts.run_intent_executor as mod

    importlib.reload(app_paths)
    importlib.reload(mod)
    return mod


def test_run_intent_executor_requires_managed_symbols(monkeypatch, tmp_path):
    mod = _reload_intent_executor(monkeypatch, tmp_path)
    monkeypatch.setattr(
        mod,
        "load_runtime_trading_config",
        lambda: {
            "execution": {"venue": "coinbase", "executor_mode": "paper"},
            "pipeline": {"exchange_id": "coinbase"},
            "symbols": [],
        },
    )

    with pytest.raises(RuntimeError) as exc:
        mod.main()

    assert str(exc.value) == "CBP_CONFIG_REQUIRED:missing_config:symbols[0]"


def test_run_intent_executor_uses_single_symbol_as_reconcile_target(monkeypatch, tmp_path):
    mod = _reload_intent_executor(monkeypatch, tmp_path)
    monkeypatch.setattr(
        mod,
        "load_runtime_trading_config",
        lambda: {
            "execution": {"venue": "coinbase", "executor_mode": "paper", "loop_interval_sec": 1, "reconcile_every_sec": 1},
            "pipeline": {"exchange_id": "coinbase"},
            "symbols": ["BTC/USD"],
        },
    )
    monkeypatch.setattr(mod, "execute_one", lambda cfg, venue, mode: None)
    monkeypatch.setattr(mod, "reconcile_open", lambda *args, **kwargs: None)
    monkeypatch.setattr(mod.time, "sleep", lambda _seconds: (_ for _ in ()).throw(KeyboardInterrupt()))

    assert mod.main() == 0

    payload = json.loads(mod.STATUS_FILE.read_text(encoding="utf-8"))
    assert payload.get("status") == "stopped"
    assert payload.get("symbol") == "BTC/USD"
    assert payload.get("symbols") == ["BTC/USD"]
