from __future__ import annotations

import sys
from pathlib import Path

import yaml

from services.supervisor import supervisor_daemon as sd


ROOT = Path(__file__).resolve().parents[1]


def test_supervisor_daemon_uses_state_data_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path / "state"))
    daemon = sd.SupervisorDaemon(cfg_path=str(tmp_path / "services.yaml"))
    assert daemon.data_dir == (tmp_path / "state" / "data" / "supervisor")


def test_supervisor_daemon_rewrites_python_cmd_to_current_interpreter(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    daemon = sd.SupervisorDaemon(cfg_path=str(tmp_path / "services.yaml"))
    daemon.root = tmp_path
    daemon.data_dir = tmp_path / "supervisor"
    daemon.pid_path = daemon.data_dir / "daemon.pid"
    daemon.stop_path = daemon.data_dir / "STOP"
    daemon.status_path = daemon.data_dir / "status.json"

    captured: dict[str, object] = {}

    class _DummyProc:
        pid = 4321

        def poll(self):
            return None

    def _fake_popen(cmd, **kwargs):
        captured["cmd"] = list(cmd)
        captured["kwargs"] = dict(kwargs)
        return _DummyProc()

    monkeypatch.setattr(sd.subprocess, "Popen", _fake_popen)
    monkeypatch.setattr(daemon, "_write_status", lambda: None)

    daemon.start_service(
        "market_ws",
        {"cmd": ["python", "scripts/run_tick_publisher.py", "run"], "cwd": str(tmp_path)},
    )

    assert captured["cmd"][0] == sys.executable


def test_services_config_enabled_services_reference_existing_scripts():
    cfg = yaml.safe_load((ROOT / "config" / "services.yaml").read_text(encoding="utf-8")) or {}
    services = cfg.get("services") or {}
    assert "ops_risk_gate" in services

    missing: list[str] = []
    for name, svc in services.items():
        if not isinstance(svc, dict):
            continue
        if not bool(svc.get("enabled", True)):
            continue
        cmd = svc.get("cmd")
        if not isinstance(cmd, list):
            missing.append(f"{name}:missing_cmd_list")
            continue
        script_tokens = [str(x) for x in cmd if isinstance(x, str) and x.startswith("scripts/") and x.endswith(".py")]
        if not script_tokens:
            missing.append(f"{name}:missing_script_token")
            continue
        for token in script_tokens:
            if not (ROOT / token).exists():
                missing.append(f"{name}:{token}")
    assert not missing, "Enabled service command references missing scripts:\n" + "\n".join(missing)
