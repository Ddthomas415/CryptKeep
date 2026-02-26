from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_check_repo_alignment_smoke():
    root = Path(__file__).resolve().parents[1]
    cmd = [sys.executable, str(root / "scripts" / "check_repo_alignment.py")]
    subprocess.check_call(cmd, cwd=str(root))
