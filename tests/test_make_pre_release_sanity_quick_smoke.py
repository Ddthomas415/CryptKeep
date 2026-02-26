from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_make_pre_release_sanity_quick_smoke():
    out = subprocess.check_output(["make", "pre-release-sanity-quick"], cwd=str(ROOT), text=True)
    assert "[OK] alignment gate passed" in out
    assert "[OK] pre-release sanity suite complete" in out
