from dashboard.services import operator

def test_run_repo_script_rejects_disallowed_script() -> None:
    rc, out = operator.run_repo_script("scripts/supervisor.py")
    assert rc == 1
    assert out == "disallowed_script"

def test_start_repo_script_background_rejects_disallowed_script() -> None:
    rc, out = operator.start_repo_script_background("scripts/supervisor.py")
    assert rc == 1
    assert out == "disallowed_script"
