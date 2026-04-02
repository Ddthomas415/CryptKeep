import subprocess
import sys
import json
import os

def test_op_stop_everything_is_enabled(tmp_path) -> None:
    env = os.environ.copy()
    env["CBP_STATE_DIR"] = str(tmp_path)
    p = subprocess.run([sys.executable, "scripts/op.py", "stop-everything"], capture_output=True, text=True, env=env)
    assert p.returncode in (0, 2)
    payload = json.loads(p.stdout)
    assert "system_guard" in payload
    assert payload.get("precedence", [])[0] == "system_guard.set_state(HALTING)"

def test_op_rejects_supervisor_start() -> None:
    p = subprocess.run([sys.executable, "scripts/op.py", "supervisor-start"], capture_output=True, text=True)
    assert p.returncode == 2
    assert "disabled_command" in p.stdout
