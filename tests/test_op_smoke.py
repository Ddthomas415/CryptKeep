from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

def run_op(args: list[str]) -> str:
    root = Path(__file__).resolve().parents[1]
    cmd = [sys.executable, str(root / "scripts" / "op.py")] + args
    out = subprocess.check_output(cmd, cwd=str(root), text=True)
    return out.strip()

def test_op_list_contains_tick_publisher():
    out = run_op(["list"])
    assert "market_ws" in out.splitlines()
    assert "tick_publisher" in out.splitlines()

def test_op_status_all_json():
    out = run_op(["status-all"])
    obj = json.loads(out)
    assert "services" in obj
    names = {x["name"] for x in obj["services"]}
    assert "market_ws" in names
    assert "tick_publisher" in names

def test_op_diag_json():
    out = run_op(["diag", "--lines", "20"])
    obj = json.loads(out)
    assert obj.get("ok") is True
    assert "services" in obj
    assert "python" in obj
