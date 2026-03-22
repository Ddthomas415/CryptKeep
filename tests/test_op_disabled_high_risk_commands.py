import subprocess
import sys

def test_op_rejects_stop_everything() -> None:
    p = subprocess.run([sys.executable, "scripts/op.py", "stop-everything"], capture_output=True, text=True)
    assert p.returncode == 2
    assert "disabled_command" in p.stdout

def test_op_rejects_supervisor_start() -> None:
    p = subprocess.run([sys.executable, "scripts/op.py", "supervisor-start"], capture_output=True, text=True)
    assert p.returncode == 2
    assert "disabled_command" in p.stdout
