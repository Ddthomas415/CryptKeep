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
        "load_user_yaml",
        lambda: {"execution": {"venue": "coinbase", "mode": "paper", "loop_interval_sec": 1, "reconcile_every_sec": 1}},
    )
    monkeypatch.setattr(mod, "execute_one", lambda cfg, venue, mode: None)
    monkeypatch.setattr(mod, "reconcile_open", lambda *args, **kwargs: None)
    monkeypatch.setattr(mod.time, "sleep", lambda _seconds: (_ for _ in ()).throw(KeyboardInterrupt()))

    assert mod.main() == 0
    payload = json.loads(mod.STATUS_FILE.read_text(encoding="utf-8"))
    assert payload.get("status") == "stopped"
    assert payload.get("venue") == "coinbase"


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
