from __future__ import annotations

from services.supervisor import supervisor as sv
from services.os.ports import PortResolution


def test_supervisor_status_includes_ops_risk_gate(monkeypatch):
    monkeypatch.setattr(sv, "ensure_dirs", lambda: None)
    monkeypatch.setattr(
        sv,
        "_read_json",
        lambda _p: {
            "pids": {
                "dashboard": 10,
                "tick_publisher": 20,
                "market_ws": 21,
                "evidence_webhook": 30,
                "ops_risk_gate": 40,
            }
        },
    )
    monkeypatch.setattr(sv, "pid_is_alive", lambda pid: int(pid) in {10, 21, 40})
    monkeypatch.setattr(sv, "_now_iso", lambda: "2026-01-01T00:00:00+00:00")

    out = sv.status()

    assert out["services"]["market_ws"]["pid"] == 21
    assert out["services"]["market_ws"]["alive"] is True
    assert out["services"]["ops_risk_gate"]["pid"] == 40
    assert out["services"]["ops_risk_gate"]["alive"] is True


def test_supervisor_start_starts_ops_risk_gate_by_default(monkeypatch):
    monkeypatch.setattr(sv, "ensure_dirs", lambda: None)
    monkeypatch.setattr(sv, "_acquire_lock", lambda: {"ok": True})
    monkeypatch.setattr(sv, "_release_lock", lambda: None)
    monkeypatch.setattr(sv, "_default_host_port", lambda: ("127.0.0.1", 8501))
    monkeypatch.setattr(sv, "_read_json", lambda _p: {})
    monkeypatch.setattr(sv, "pid_is_alive", lambda _pid: False)
    monkeypatch.setattr(sv, "_open_browser", lambda _host, _port: None)

    captured: dict[str, object] = {}
    cmds: list[list[str]] = []

    def _spawn(cmd: list[str]) -> int:
        cmds.append(list(cmd))
        return 1000 + len(cmds)

    monkeypatch.setattr(sv, "_spawn_detached", _spawn)
    monkeypatch.setattr(
        sv,
        "_write_state",
        lambda pids, meta: captured.update({"pids": dict(pids), "meta": dict(meta)}),
    )

    out = sv.start(with_dashboard=False, open_browser=False, start_risk_gate=True)

    assert out.get("ok") is True
    assert captured["pids"]["market_ws"] == 1002
    assert captured["pids"]["ops_signal_adapter"] == 1004
    assert captured["pids"]["ops_risk_gate"] == 1005
    assert captured["meta"]["start_market_ws"] is True
    assert captured["meta"]["start_signal_adapter"] is True
    assert captured["meta"]["start_risk_gate"] is True
    ws_cmds = [c for c in cmds if "run_ws_ticker_feed_safe.py" in " ".join(c)]
    assert ws_cmds
    assert ws_cmds[0][-1] == "run"
    risk_cmds = [c for c in cmds if "run_ops_risk_gate_service.py" in " ".join(c)]
    assert risk_cmds
    assert risk_cmds[0][-1] == "run"

    sig_cmds = [c for c in cmds if "run_ops_signal_adapter.py" in " ".join(c)]
    assert sig_cmds
    assert sig_cmds[0][-1] == "run"


def test_supervisor_stop_writes_ops_risk_gate_stop_flag(monkeypatch, tmp_path):
    rt = tmp_path / "runtime"

    def _ensure_dirs() -> None:
        (rt / "flags").mkdir(parents=True, exist_ok=True)
        (rt / "locks").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(sv, "ensure_dirs", _ensure_dirs)
    monkeypatch.setattr(sv, "runtime_dir", lambda: rt)
    monkeypatch.setattr(sv, "_acquire_lock", lambda: {"ok": True})
    monkeypatch.setattr(sv, "_release_lock", lambda: None)
    monkeypatch.setattr(sv, "_read_json", lambda _p: {"pids": {"ops_risk_gate": 901}})
    monkeypatch.setattr(sv, "pid_is_alive", lambda _pid: False)
    monkeypatch.setattr(sv, "status", lambda: {"ok": True, "services": {}})

    captured: dict[str, object] = {}
    monkeypatch.setattr(
        sv,
        "_write_state",
        lambda pids, meta: captured.update({"pids": dict(pids), "meta": dict(meta)}),
    )

    out = sv.stop(stop_dashboard=False, stop_tick=False, stop_webhook=False, stop_risk_gate=True, timeout_sec=0)

    assert out.get("ok") is True
    assert (rt / "flags" / "ops_risk_gate_service.stop").exists()
    assert captured["pids"]["ops_risk_gate"] == 0
    assert any(a.get("service") == "ops_risk_gate" and a.get("action") == "stop_file_written" for a in out.get("actions", []))


def test_supervisor_stop_writes_market_ws_stop_flag(monkeypatch, tmp_path):
    rt = tmp_path / "runtime"

    def _ensure_dirs() -> None:
        (rt / "flags").mkdir(parents=True, exist_ok=True)
        (rt / "locks").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(sv, "ensure_dirs", _ensure_dirs)
    monkeypatch.setattr(sv, "runtime_dir", lambda: rt)
    monkeypatch.setattr(sv, "_acquire_lock", lambda: {"ok": True})
    monkeypatch.setattr(sv, "_release_lock", lambda: None)
    monkeypatch.setattr(sv, "_read_json", lambda _p: {"pids": {"market_ws": 903}})
    monkeypatch.setattr(sv, "pid_is_alive", lambda _pid: False)
    monkeypatch.setattr(sv, "status", lambda: {"ok": True, "services": {}})

    captured: dict[str, object] = {}
    monkeypatch.setattr(
        sv,
        "_write_state",
        lambda pids, meta: captured.update({"pids": dict(pids), "meta": dict(meta)}),
    )

    out = sv.stop(stop_dashboard=False, stop_tick=True, stop_webhook=False, stop_signal_adapter=False, stop_risk_gate=False, timeout_sec=0)

    assert out.get("ok") is True
    assert (rt / "flags" / "market_ws.stop").exists()
    assert captured["pids"]["market_ws"] == 0
    assert any(a.get("service") == "market_ws" and a.get("action") == "stop_file_written" for a in out.get("actions", []))


def test_supervisor_stop_writes_ops_signal_adapter_stop_flag(monkeypatch, tmp_path):
    rt = tmp_path / "runtime"

    def _ensure_dirs() -> None:
        (rt / "flags").mkdir(parents=True, exist_ok=True)
        (rt / "locks").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(sv, "ensure_dirs", _ensure_dirs)
    monkeypatch.setattr(sv, "runtime_dir", lambda: rt)
    monkeypatch.setattr(sv, "_acquire_lock", lambda: {"ok": True})
    monkeypatch.setattr(sv, "_release_lock", lambda: None)
    monkeypatch.setattr(sv, "_read_json", lambda _p: {"pids": {"ops_signal_adapter": 902}})
    monkeypatch.setattr(sv, "pid_is_alive", lambda _pid: False)
    monkeypatch.setattr(sv, "status", lambda: {"ok": True, "services": {}})

    captured: dict[str, object] = {}
    monkeypatch.setattr(
        sv,
        "_write_state",
        lambda pids, meta: captured.update({"pids": dict(pids), "meta": dict(meta)}),
    )

    out = sv.stop(
        stop_dashboard=False,
        stop_tick=False,
        stop_webhook=False,
        stop_signal_adapter=True,
        stop_risk_gate=False,
        timeout_sec=0,
    )

    assert out.get("ok") is True
    assert (rt / "flags" / "ops_signal_adapter.stop").exists()
    assert captured["pids"]["ops_signal_adapter"] == 0
    assert any(
        a.get("service") == "ops_signal_adapter" and a.get("action") == "stop_file_written"
        for a in out.get("actions", [])
    )


def test_supervisor_start_auto_switches_dashboard_port(monkeypatch):
    monkeypatch.setattr(sv, "ensure_dirs", lambda: None)
    monkeypatch.setattr(sv, "_acquire_lock", lambda: {"ok": True})
    monkeypatch.setattr(sv, "_release_lock", lambda: None)
    monkeypatch.setattr(sv, "_default_host_port", lambda: ("127.0.0.1", 8501))
    monkeypatch.setattr(
        sv,
        "resolve_preferred_port",
        lambda host, port, max_offset=50: PortResolution(
            host=str(host),
            requested_port=int(port),
            resolved_port=8502,
            requested_available=False,
            auto_switched=True,
        ),
    )
    monkeypatch.setattr(sv, "_read_json", lambda _p: {})
    monkeypatch.setattr(sv, "pid_is_alive", lambda _pid: False)
    monkeypatch.setattr(sv, "_open_browser", lambda _host, _port: None)

    captured: dict[str, object] = {}
    cmds: list[list[str]] = []

    def _spawn(cmd: list[str]) -> int:
        cmds.append(list(cmd))
        return 2000 + len(cmds)

    monkeypatch.setattr(sv, "_spawn_detached", _spawn)
    monkeypatch.setattr(
        sv,
        "_write_state",
        lambda pids, meta: captured.update({"pids": dict(pids), "meta": dict(meta)}),
    )

    out = sv.start(open_browser=False)

    dashboard_cmds = [c for c in cmds if "streamlit" in " ".join(c)]
    assert out["ok"] is True
    assert out["port_resolution"]["resolved_port"] == 8502
    assert out["port_resolution"]["auto_switched"] is True
    assert captured["meta"]["port"] == 8502
    assert captured["meta"]["requested_port"] == 8501
    assert captured["meta"]["auto_switched_port"] is True
    assert dashboard_cmds
    assert dashboard_cmds[0][-1] == "8502"
