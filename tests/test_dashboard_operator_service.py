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
