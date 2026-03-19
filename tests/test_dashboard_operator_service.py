from __future__ import annotations

from types import SimpleNamespace

from dashboard.services import operator as operator_service


def test_list_services_parses_cli_output(monkeypatch):
    monkeypatch.setattr(
        operator_service,
        "run_op",
        lambda _args: (0, "tick_publisher\nintent_reconciler\nintent_executor\n"),
    )
    out = operator_service.list_services()
    assert out == ["tick_publisher", "intent_reconciler", "intent_executor"]


def test_list_services_fallback_when_cli_fails(monkeypatch):
    monkeypatch.setattr(operator_service, "run_op", lambda _args: (2, "boom"))
    out = operator_service.list_services(fallback=["svc_a", "svc_b"])
    assert out == ["svc_a", "svc_b"]


def test_run_op_returns_rc_and_combined_output(monkeypatch):
    def fake_run(*_args, **_kwargs):
        return SimpleNamespace(returncode=3, stdout="hello\n", stderr="world\n")

    monkeypatch.setattr(operator_service.subprocess, "run", fake_run)
    rc, out = operator_service.run_op(["status-all"])
    assert rc == 3
    assert "hello" in out
    assert "world" in out


def test_run_repo_script_returns_rc_and_combined_output(monkeypatch):
    def fake_run(*_args, **_kwargs):
        return SimpleNamespace(returncode=1, stdout='{"ok":false}\n', stderr="warn\n")

    monkeypatch.setattr(operator_service.subprocess, "run", fake_run)
    rc, out = operator_service.run_repo_script("scripts/show_live_gate_inputs.py")
    assert rc == 1
    assert '{"ok":false}' in out
    assert "warn" in out


def test_start_repo_script_background_returns_started_pid(monkeypatch):
    seen: dict[str, object] = {}

    class _Proc:
        pid = 43210

    def fake_popen(cmd, **kwargs):
        seen["cmd"] = cmd
        seen["kwargs"] = kwargs
        return _Proc()

    monkeypatch.setattr(operator_service.subprocess, "Popen", fake_popen)
    rc, out = operator_service.start_repo_script_background(
        "scripts/run_crypto_edge_collector_loop.py",
        args=["--stop"],
    )

    assert rc == 0
    assert "started pid=43210" in out
    assert "run_crypto_edge_collector_loop.py" in " ".join(str(x) for x in seen["cmd"])


def test_start_crypto_edge_collector_loop_returns_already_running(monkeypatch):
    monkeypatch.setattr(
        "services.analytics.crypto_edge_collector_service.load_runtime_status",
        lambda: {"ok": True, "pid_alive": True, "pid": 23456, "status": "running"},
    )

    rc, out = operator_service.start_crypto_edge_collector_loop(interval_sec=900.0)

    assert rc == 0
    assert "already running" in out
    assert "23456" in out


def test_start_crypto_edge_collector_loop_uses_background_runner(monkeypatch):
    monkeypatch.setattr(
        "services.analytics.crypto_edge_collector_service.load_runtime_status",
        lambda: {"ok": True, "pid_alive": False, "status": "dead"},
    )
    monkeypatch.setattr(
        operator_service,
        "start_repo_script_background",
        lambda script_relpath, args=None: (0, f"{script_relpath}|{' '.join(str(x) for x in (args or []))}"),
    )

    rc, out = operator_service.start_crypto_edge_collector_loop(interval_sec=900.0)

    assert rc == 0
    assert "scripts/run_crypto_edge_collector_loop.py" in out
    assert "--interval-sec 900" in out


def test_get_operations_snapshot_summarizes_services_and_health(monkeypatch):
    monkeypatch.setattr(operator_service, "list_services", lambda fallback=None: ["tick_publisher", "intent_executor"])
    monkeypatch.setattr(
        "services.admin.health.list_health",
        lambda: [
            {"service": "tick_publisher", "status": "RUNNING", "ts": "2026-03-12T10:00:00Z"},
            {"service": "intent_executor", "status": "ERROR", "ts": "2026-03-12T10:05:00Z"},
            {"service": "audit_tail", "status": "STARTING", "ts": "2026-03-12T09:58:00Z"},
        ],
    )

    payload = operator_service.get_operations_snapshot()
    assert payload == {
        "services": ["tick_publisher", "intent_executor", "audit_tail"],
        "tracked_services": 3,
        "healthy_services": 2,
        "attention_services": 1,
        "unknown_services": 0,
        "last_health_ts": "2026-03-12T10:05:00Z",
    }


def test_run_full_system_diagnostics_wraps_core_service(monkeypatch):
    monkeypatch.setattr(
        "services.admin.system_diagnostics.run_full_diagnostics",
        lambda export_bundle=False: {"ok": True, "status": "warn", "export_bundle": export_bundle},
    )

    out = operator_service.run_full_system_diagnostics(export_bundle=True)

    assert out["ok"] is True
    assert out["status"] == "warn"
    assert out["export_bundle"] is True


def test_apply_safe_system_self_repair_wraps_core_service(monkeypatch):
    monkeypatch.setattr(
        "services.admin.system_diagnostics.apply_safe_self_repair",
        lambda export_bundle=True: {"ok": True, "removed_count": 2, "export_bundle": export_bundle},
    )

    out = operator_service.apply_safe_system_self_repair(export_bundle=False)

    assert out["ok"] is True
    assert out["removed_count"] == 2
    assert out["export_bundle"] is False


def test_run_dashboard_streamlit_diagnostics_wraps_app_service(monkeypatch):
    monkeypatch.setattr(
        "services.app.dashboard_diagnostics.run_dashboard_diagnostics",
        lambda startup_smoke=True, timeout_sec=15.0: {
            "ok": True,
            "status": "ok",
            "startup_smoke": startup_smoke,
            "timeout_sec": timeout_sec,
        },
    )

    out = operator_service.run_dashboard_streamlit_diagnostics(startup_smoke=False, timeout_sec=7.5)

    assert out["ok"] is True
    assert out["status"] == "ok"
    assert out["startup_smoke"] is False
    assert out["timeout_sec"] == 7.5
