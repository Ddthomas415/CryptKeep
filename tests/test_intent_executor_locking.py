from __future__ import annotations

import importlib
import json
import os


def _reload_intent_executor(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path / "state"))
    import services.os.app_paths as app_paths
    import scripts.run_intent_executor as mod

    importlib.reload(app_paths)
    importlib.reload(mod)
    return mod


def test_intent_executor_reclaims_dead_pid_lock(monkeypatch, tmp_path):
    mod = _reload_intent_executor(monkeypatch, tmp_path)
    mod.LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    mod.LOCK_FILE.write_text(json.dumps({"pid": 999999999, "ts_epoch": 0}) + "\n", encoding="utf-8")

    assert mod._acquire_lock()

    payload = json.loads(mod.LOCK_FILE.read_text(encoding="utf-8"))
    assert payload["pid"] == os.getpid()
    mod._release_lock()


def test_intent_executor_preserves_live_pid_lock(monkeypatch, tmp_path):
    mod = _reload_intent_executor(monkeypatch, tmp_path)
    mod.LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    mod.LOCK_FILE.write_text(json.dumps({"pid": os.getpid(), "ts_epoch": 1}) + "\n", encoding="utf-8")

    assert not mod._acquire_lock()
    assert json.loads(mod.LOCK_FILE.read_text(encoding="utf-8"))["pid"] == os.getpid()
