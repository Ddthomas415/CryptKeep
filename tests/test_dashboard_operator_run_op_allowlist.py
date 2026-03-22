from dashboard.services import operator

def test_run_op_rejects_supervisor_start() -> None:
    rc, out = operator.run_op(["supervisor-start"], current_role="OPERATOR")
    assert rc == 1
    assert out == "disallowed_op"

def test_run_op_rejects_stop_everything() -> None:
    rc, out = operator.run_op(["stop-everything"], current_role="OPERATOR")
    assert rc == 1
    assert out == "disallowed_op"
