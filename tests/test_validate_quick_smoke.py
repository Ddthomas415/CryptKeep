from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_validate_quick_smoke():
    root = Path(__file__).resolve().parents[1]
    cmd = [sys.executable, str(root / "scripts" / "validate.py"), "--quick"]
    subprocess.check_call(cmd, cwd=str(root))
