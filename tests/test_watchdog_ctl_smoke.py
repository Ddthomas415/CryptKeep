from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    root = Path(__file__).resolve().parents[1]
    cmd = [sys.executable, str(root / "scripts" / "watchdog_ctl.py")] + args
    return subprocess.run(cmd, cwd=str(root), text=True, capture_output=True)


def test_watchdog_ctl_status_smoke():
    p = _run(["status"])
    assert p.returncode == 0
    payload = ast.literal_eval(p.stdout.strip())
    assert payload.get("ok") is True
    assert "running" in payload


def test_watchdog_ctl_clear_stale_shape():
    p = _run(["clear_stale", "--hard"])
    assert p.returncode == 0
    payload = ast.literal_eval(p.stdout.strip())
    assert payload.get("ok") is True
    assert isinstance(payload.get("watchdog"), dict)
    assert isinstance(payload.get("locks"), dict)
