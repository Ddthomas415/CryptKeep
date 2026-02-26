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
    required = {
        "adapters",
        "attic",
        "config",
        "core",
        "dashboard",
        "desktop",
        "docker",
        "docs",
        "scripts",
        "services",
        "src-tauri",
        "storage",
        "tests",
        "tools",
    }
    assert required.issubset(canonical_present)
