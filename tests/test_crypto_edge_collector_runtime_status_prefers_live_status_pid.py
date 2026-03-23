import json
from services.analytics import crypto_edge_collector_service as mod

def test_runtime_status_prefers_live_status_pid(tmp_path, monkeypatch):
    health = tmp_path / "health"
    health.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(mod, "status_file", lambda: health / "crypto_edge_collector.json")
    monkeypatch.setattr(mod, "pid_file", lambda: health / "crypto_edge_collector.pid.json")
    monkeypatch.setattr(mod, "_process_alive", lambda pid: pid == 99999)

    (health / "crypto_edge_collector.json").write_text(json.dumps({
        "ok": True,
        "status": "running",
        "pid": 99999,
        "source": "live_public",
        "last_ok": True,
    }))
    (health / "crypto_edge_collector.pid.json").write_text(json.dumps({
        "pid": 11111,
        "started_ts": "old",
        "poll_interval_sec": 300.0,
        "source": "live_public",
    }))

    out = mod.load_runtime_status()
    assert out["status"] == "running"
    assert out["pid"] == 99999
    assert out["pid_alive"] is True
