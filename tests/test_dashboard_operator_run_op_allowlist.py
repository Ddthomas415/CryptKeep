from dashboard.services import operator

def test_run_op_rejects_supervisor_start() -> None:
    rc, out = operator.run_op(["supervisor-start"], current_role="OPERATOR")
    assert rc == 1
    assert out == "disallowed_op"

def test_run_op_allows_stop_everything(monkeypatch) -> None:
    class _Proc:
        returncode = 0
        stdout = '{"ok": true}\n'
        stderr = ""

    monkeypatch.setattr(operator.subprocess, "run", lambda *args, **kwargs: _Proc())

    rc, out = operator.run_op(["stop-everything"], current_role="OPERATOR")

    assert rc == 0
    assert '{"ok": true}' in out
