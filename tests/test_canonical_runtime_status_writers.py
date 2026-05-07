from __future__ import annotations

import importlib
import json


def _reload_intent_executor(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path / "state"))
    import services.os.app_paths as app_paths
    import scripts.run_intent_executor as mod

    importlib.reload(app_paths)
    importlib.reload(mod)
    return mod


def _reload_pipeline_loop(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path / "state"))
    import services.os.app_paths as app_paths
    import scripts.run_pipeline_loop as mod

    importlib.reload(app_paths)
    importlib.reload(mod)
    return mod


def test_run_intent_executor_writes_status_file(monkeypatch, tmp_path):
    mod = _reload_intent_executor(monkeypatch, tmp_path)
    monkeypatch.setattr(
        mod,
        "load_runtime_trading_config",
        lambda: {"execution": {"venue": "coinbase", "mode": "paper", "loop_interval_sec": 1, "reconcile_every_sec": 1}},
    )
    monkeypatch.setattr(mod, "execute_one", lambda cfg, venue, mode: None)
    monkeypatch.setattr(mod, "reconcile_open", lambda *args, **kwargs: None)
    monkeypatch.setattr(mod.time, "sleep", lambda _seconds: (_ for _ in ()).throw(KeyboardInterrupt()))

    assert mod.main() == 0
    payload = json.loads(mod.STATUS_FILE.read_text(encoding="utf-8"))
    assert payload.get("status") == "stopped"
    assert payload.get("venue") == "coinbase"
    assert not mod.LOCK_FILE.exists()


def test_run_intent_executor_uses_full_symbol_set_for_multi_symbol_reconcile(monkeypatch, tmp_path):
    mod = _reload_intent_executor(monkeypatch, tmp_path)
    monkeypatch.setattr(
        mod,
        "load_runtime_trading_config",
        lambda: {
            "execution": {
                "venue": "coinbase",
                "mode": "paper",
                "loop_interval_sec": 1,
                "reconcile_every_sec": 1,
                "symbols": ["BTC/USD", "ETH/USD"],
            },
            "pipeline": {"symbols": ["BTC/USD", "ETH/USD"]},
        },
    )
    monkeypatch.setattr(mod, "execute_one", lambda cfg, venue, mode: None)
    reconcile_calls: list[dict] = []
    monkeypatch.setattr(
        mod,
        "reconcile_open",
        lambda cfg, venue, mode, symbol=None, limit=400: reconcile_calls.append(
            {"venue": venue, "mode": mode, "symbol": symbol, "limit": limit}
        ),
    )
    monkeypatch.setattr(mod.time, "sleep", lambda _seconds: (_ for _ in ()).throw(KeyboardInterrupt()))

    assert mod.main() == 0
    payload = json.loads(mod.STATUS_FILE.read_text(encoding="utf-8"))
    assert payload.get("symbols") == ["BTC/USD", "ETH/USD"]
    assert reconcile_calls
    assert reconcile_calls[0]["symbol"] is None


def test_run_intent_executor_writes_lock_exists_status(monkeypatch, tmp_path):
    mod = _reload_intent_executor(monkeypatch, tmp_path)
    monkeypatch.setattr(mod, "_acquire_lock", lambda: False)

    assert mod.main() == 0

    payload = json.loads(mod.STATUS_FILE.read_text(encoding="utf-8"))
    assert payload.get("reason") == "lock_exists"
    assert payload.get("lock_file") == str(mod.LOCK_FILE)


def test_run_pipeline_loop_writes_status_file(monkeypatch, tmp_path):
    mod = _reload_pipeline_loop(monkeypatch, tmp_path)
    monkeypatch.setattr(
        mod,
        "load_runtime_trading_config",
        lambda: {
            "pipeline": {"poll_sec": 1, "exchange_id": "coinbase", "strategy": "ema"},
            "execution": {"executor_mode": "paper"},
            "symbols": ["BTC/USD"],
        },
    )

    class _DummyPipeline:
        cfg = type("_Cfg", (), {"exchange_id": "coinbase"})()

        def run_once(self):
            return {"ok": True}

    monkeypatch.setattr(mod, "build_pipeline", lambda _cfg: _DummyPipeline())
    monkeypatch.setattr(mod.time, "sleep", lambda _seconds: (_ for _ in ()).throw(KeyboardInterrupt()))

    assert mod.main() == 0
    payload = json.loads(mod.STATUS_FILE.read_text(encoding="utf-8"))
    assert payload.get("status") == "stopped"
    assert payload.get("exchange") == "coinbase"
    assert payload.get("symbols") == ["BTC/USD"]


def test_run_pipeline_loop_survives_iteration_error(monkeypatch, tmp_path):
    mod = _reload_pipeline_loop(monkeypatch, tmp_path)
    monkeypatch.setattr(
        mod,
        "load_runtime_trading_config",
        lambda: {
            "pipeline": {"poll_sec": 1, "exchange_id": "coinbase", "strategy": "ema"},
            "execution": {"executor_mode": "paper"},
            "symbols": ["BTC/USD"],
        },
    )

    class _DummyPipeline:
        cfg = type("_Cfg", (), {"exchange_id": "coinbase"})()

        def __init__(self):
            self.calls = 0

        def run_once(self):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("temporary_feed_error")
            return {"ok": True, "note": "recovered"}

    pipeline = _DummyPipeline()
    statuses: list[dict] = []

    monkeypatch.setattr(mod, "build_pipeline", lambda _cfg: pipeline)
    monkeypatch.setattr(mod, "_write_status", lambda payload: statuses.append(dict(payload)))

    sleep_calls = {"count": 0}

    def _sleep(_seconds):
        sleep_calls["count"] += 1
        if sleep_calls["count"] >= 2:
            raise KeyboardInterrupt()

    monkeypatch.setattr(mod.time, "sleep", _sleep)

    assert mod.main() == 0
    assert pipeline.calls == 2
    assert any(
        payload.get("status") == "running"
        and payload.get("last_ok") is False
        and payload.get("last_result", {}).get("error_type") == "RuntimeError"
        for payload in statuses
    )
    assert statuses[-1].get("status") == "stopped"
    assert statuses[-1].get("errors") == 1
    assert statuses[-1].get("loops") == 1


def test_run_pipeline_loop_fans_out_across_symbols(monkeypatch, tmp_path):
    mod = _reload_pipeline_loop(monkeypatch, tmp_path)
    monkeypatch.setattr(
        mod,
        "load_runtime_trading_config",
        lambda: {
            "pipeline": {"poll_sec": 1, "exchange_id": "coinbase", "strategy": "ema", "symbols": ["BTC/USD", "ETH/USD"]},
            "execution": {"executor_mode": "paper", "symbols": ["BTC/USD", "ETH/USD"]},
            "symbols": ["BTC/USDT", "ETH/USDT"],
        },
    )

    built: list[str] = []

    class _DummyPipeline:
        cfg = type("_Cfg", (), {"exchange_id": "coinbase"})()

        def __init__(self, symbol: str):
            self.symbol = symbol

        def run_once(self):
            return {"ok": True, "note": f"ran:{self.symbol}"}

    monkeypatch.setattr(mod, "build_pipeline", lambda cfg: built.append(cfg.symbol) or _DummyPipeline(cfg.symbol))
    monkeypatch.setattr(mod.time, "sleep", lambda _seconds: (_ for _ in ()).throw(KeyboardInterrupt()))

    assert mod.main() == 0
    payload = json.loads(mod.STATUS_FILE.read_text(encoding="utf-8"))
    assert built == ["BTC/USD", "ETH/USD"]
    assert payload.get("symbols") == ["BTC/USD", "ETH/USD"]
    assert payload.get("last_result", {}).get("note") == "multi_symbol_cycle"
