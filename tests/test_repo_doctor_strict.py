from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_repo_doctor_strict_is_clean():
    root = Path(__file__).resolve().parents[1]
    cmd = [sys.executable, str(root / "tools" / "repo_doctor.py"), "--strict", "--json"]
    out = subprocess.check_output(cmd, cwd=str(root), text=True)
    payload = json.loads(out)
    assert payload.get("noncanonical_top_level_dirs") == []
    assert payload.get("suspicious_top_level_files") == []
    canonical_present = set(payload.get("canonical_present") or [])
    baseline_present = set(payload.get("supported_baseline_present") or [])
    allowed_present = set(payload.get("allowed_top_level_present") or [])
    required = {
        "adapters",
        "core",
        "dashboard",
        "docker",
        "docs",
        "scripts",
        "services",
        "storage",
        "tests",
    }
    assert baseline_present == canonical_present
    assert required.issubset(baseline_present)
    assert {"config", "desktop", "src-tauri", "tools"}.issubset(allowed_present)
    assert {"attic", "build", "crypto-trading-ai", "desktop", "src-tauri"}.isdisjoint(baseline_present)
