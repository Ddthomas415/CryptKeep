from __future__ import annotations

import importlib
import json
from pathlib import Path


def _reload_crash_snapshot(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path / "state"))
    import services.os.app_paths as app_paths
    import services.process.crash_snapshot as mod

    importlib.reload(app_paths)
    importlib.reload(mod)
    return mod


def test_write_crash_snapshot_captures_canonical_managed_service_logs(monkeypatch, tmp_path):
    mod = _reload_crash_snapshot(monkeypatch, tmp_path)
    monkeypatch.setattr(mod, "read_heartbeat", lambda: {"ts_epoch": 123.0, "source": "test"})

    mod.BOT_LOG.parent.mkdir(parents=True, exist_ok=True)
    mod.BOT_LOG.write_text("legacy bot log\n", encoding="utf-8")

    app_log = Path(mod.app_log_path())
    app_log.write_text("app logger\n", encoding="utf-8")

    managed_logs = mod._managed_service_logs()
    managed_logs["market_ws"].parent.mkdir(parents=True, exist_ok=True)
    managed_logs["market_ws"].write_text("market ws log\n", encoding="utf-8")
    managed_logs["intent_consumer"].write_text("intent consumer log\n", encoding="utf-8")
    managed_logs["reconciler"].write_text("reconciler log\n", encoding="utf-8")

    out = mod.write_crash_snapshot(reason="test_crash_snapshot")

    assert out == {"ok": True, "path": str(mod.CRASH_PATH)}

    payload = json.loads(mod.CRASH_PATH.read_text(encoding="utf-8"))
    assert payload.get("reason") == "test_crash_snapshot"
    assert payload.get("heartbeat_last") == {"ts_epoch": 123.0, "source": "test"}
    assert payload.get("bot_log_path") == str(mod.BOT_LOG)
    assert payload.get("bot_log_tail") == "legacy bot log\n"
    assert payload.get("app_log_path") == str(app_log)
    assert payload.get("app_log_tail") == "app logger\n"
    assert payload.get("managed_service_log_tails") == {
        "market_ws": {
            "path": str(managed_logs["market_ws"]),
            "tail": "market ws log\n",
        },
        "intent_consumer": {
            "path": str(managed_logs["intent_consumer"]),
            "tail": "intent consumer log\n",
        },
        "reconciler": {
            "path": str(managed_logs["reconciler"]),
            "tail": "reconciler log\n",
        },
    }
