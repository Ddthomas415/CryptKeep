from __future__ import annotations

import subprocess
import sys
from pathlib import Path

def test_service_ctl_list_has_tick_publisher():
    root = Path(__file__).resolve().parents[1]
    cmd = [sys.executable, str(root / "scripts" / "service_ctl.py"), "list"]
    out = subprocess.check_output(cmd, cwd=str(root), text=True)
    services = {line.strip() for line in out.splitlines() if line.strip()}
    assert "tick_publisher" in services
    assert "ops_signal_adapter" in services
    assert "ops_risk_gate" in services
