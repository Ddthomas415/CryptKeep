from __future__ import annotations

import importlib
import json


def _reload_bot_runtime_truth(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path / "state"))
    import services.os.app_paths as app_paths
    import services.process.bot_runtime_truth as brt

    importlib.reload(app_paths)
    importlib.reload(brt)
    return brt


def _status_map(**running):
    names = (
        "pipeline",
        "executor",
        "intent_consumer",
        "ops_signal_adapter",
        "ops_risk_gate",
        "reconciler",
        "market_ws",
        "ai_alert_monitor",
    )
    out = {}
    for idx, name in enumerate(names, start=1):
        alive = bool(running.get(name, False))
        out[name] = {"running": alive, "pid": 1000 + idx if alive else None}
    return out


def test_canonical_bot_status_prefers_process_supervisor(monkeypatch, tmp_path):
    brt = _reload_bot_runtime_truth(monkeypatch, tmp_path)
    monkeypatch.setattr(brt, "supervisor_status", lambda _names: _status_map(intent_consumer=True))

    out = brt.canonical_bot_status()

    assert out.get("running") is True
    assert out.get("source") == "canonical_process_supervisor"
    assert out.get("state", {}).get("services", {}).get("intent_consumer", {}).get("running") is True


def test_canonical_bot_status_does_not_silently_fallback_by_default(monkeypatch, tmp_path):
    brt = _reload_bot_runtime_truth(monkeypatch, tmp_path)
    monkeypatch.setattr(brt, "supervisor_status", lambda _names: _status_map())

    class _LegacyBotProcess:
        @staticmethod
        def status():
            raise AssertionError("legacy status fallback should not be called by default")

    monkeypatch.setitem(__import__("sys").modules, "services.process.bot_process", _LegacyBotProcess)

    out = brt.canonical_bot_status()

    assert out.get("running") is False
    assert out.get("source") == "canonical_process_supervisor"
    assert out.get("legacy_fallback_enabled") is False
    assert out.get("note") == "no_canonical_running_services"


def test_canonical_bot_status_does_not_treat_market_ws_as_bot_running_alone(monkeypatch, tmp_path):
    brt = _reload_bot_runtime_truth(monkeypatch, tmp_path)
    monkeypatch.setattr(brt, "supervisor_status", lambda _names: _status_map(market_ws=True))

    out = brt.canonical_bot_status()

    assert out.get("running") is False
    assert out.get("note") == "no_canonical_running_services"
    assert out.get("state", {}).get("services", {}).get("market_ws", {}).get("running") is True


def test_read_heartbeat_prefers_latest_canonical_status(monkeypatch, tmp_path):
    brt = _reload_bot_runtime_truth(monkeypatch, tmp_path)
    monkeypatch.setattr(brt, "supervisor_status", lambda _names: _status_map(executor=True))
    monkeypatch.setattr(brt.legacy_heartbeat, "read_heartbeat", lambda: {"ts_epoch": 1.0, "source": "legacy"})

    brt.CANONICAL_STATUS_FILES["bot_runner"].parent.mkdir(parents=True, exist_ok=True)
    brt.CANONICAL_STATUS_FILES["executor"].parent.mkdir(parents=True, exist_ok=True)
    brt.CANONICAL_STATUS_FILES["bot_runner"].write_text(
        json.dumps({"status": "running", "ts_epoch": 5.0}),
        encoding="utf-8",
    )
    brt.CANONICAL_STATUS_FILES["executor"].write_text(
        json.dumps({"status": "running", "ts_epoch": 20.0}),
        encoding="utf-8",
    )

    out = brt.read_heartbeat()

    assert out.get("source") == "executor"
    assert out.get("ts_epoch") == 20.0
    assert out.get("path") == str(brt.CANONICAL_STATUS_FILES["executor"])


def test_read_heartbeat_can_use_market_ws_status_when_running(monkeypatch, tmp_path):
    brt = _reload_bot_runtime_truth(monkeypatch, tmp_path)
    monkeypatch.setattr(brt, "supervisor_status", lambda _names: _status_map(market_ws=True))

    brt.CANONICAL_STATUS_FILES["market_ws"].parent.mkdir(parents=True, exist_ok=True)
    brt.CANONICAL_STATUS_FILES["market_ws"].write_text(
        json.dumps({"status": "running", "ts": "2026-04-29T10:00:00+00:00"}),
        encoding="utf-8",
    )

    out = brt.read_heartbeat()

    assert out.get("source") == "market_ws"
    assert out.get("path") == str(brt.CANONICAL_STATUS_FILES["market_ws"])


def test_read_heartbeat_does_not_silently_fallback_by_default(monkeypatch, tmp_path):
    brt = _reload_bot_runtime_truth(monkeypatch, tmp_path)
    monkeypatch.setattr(brt, "supervisor_status", lambda _names: _status_map())
    monkeypatch.setattr(brt.legacy_heartbeat, "read_heartbeat", lambda: (_ for _ in ()).throw(AssertionError("legacy heartbeat fallback should not be called by default")))

    out = brt.read_heartbeat()

    assert out == {
        "source": "canonical_status_files",
        "legacy_fallback_enabled": False,
        "note": "no_canonical_status_signal",
    }


def test_stop_bot_uses_canonical_managed_services(monkeypatch, tmp_path):
    brt = _reload_bot_runtime_truth(monkeypatch, tmp_path)
    monkeypatch.setattr(brt, "supervisor_status", lambda _names: _status_map(executor=True, reconciler=True))

    calls: list[str] = []
    monkeypatch.setattr(brt, "disable_live_now", lambda note="": {"ok": True, "note": note})
    monkeypatch.setattr(brt, "stop_process", lambda name: calls.append(str(name)) or {"ok": True, "name": name})

    out = brt.stop_bot()

    assert out.get("mode") == "canonical"
    assert calls == ["executor", "reconciler"]
    assert out.get("disable_live", {}).get("note") == "watchdog:heartbeat_stale"


def test_stop_bot_does_not_silently_fallback_by_default(monkeypatch, tmp_path):
    brt = _reload_bot_runtime_truth(monkeypatch, tmp_path)
    monkeypatch.setattr(brt, "supervisor_status", lambda _names: _status_map())

    out = brt.stop_bot()

    assert out == {
        "ok": True,
        "mode": "canonical",
        "running": [],
        "results": [],
        "legacy_fallback_enabled": False,
        "note": "no_canonical_running_services",
    }


def test_legacy_runtime_fallback_can_be_enabled_explicitly(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_ALLOW_LEGACY_BOT_RUNTIME_FALLBACK", "YES")
    brt = _reload_bot_runtime_truth(monkeypatch, tmp_path)
    monkeypatch.setattr(brt, "supervisor_status", lambda _names: _status_map())
    monkeypatch.setattr(brt.legacy_heartbeat, "read_heartbeat", lambda: {"ts_epoch": 7.0, "source": "legacy"})

    class _LegacyBotProcess:
        @staticmethod
        def status():
            return {"ok": True, "running": True, "pid": 88}

        @staticmethod
        def stop_bot(*, hard: bool = True):
            return {"ok": True, "stopped": True, "hard": hard}

    monkeypatch.setitem(__import__("sys").modules, "services.process.bot_process", _LegacyBotProcess)

    status_out = brt.canonical_bot_status()
    heartbeat_out = brt.read_heartbeat()
    stop_out = brt.stop_bot()

    assert status_out.get("source") == "legacy_bot_process_fallback"
    assert status_out.get("compatibility_only") is True
    assert heartbeat_out.get("source") == "legacy_heartbeat_fallback"
    assert heartbeat_out.get("legacy_fallback_enabled") is True
    assert stop_out.get("source") == "legacy_bot_process_fallback"
    assert stop_out.get("compatibility_only") is True
