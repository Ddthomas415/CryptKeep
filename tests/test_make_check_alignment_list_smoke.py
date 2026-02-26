from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_make_check_alignment_list_smoke():
    out = subprocess.check_output(["make", "check-alignment-list"], cwd=str(ROOT), text=True)
    lines = [ln.strip() for ln in out.splitlines() if ln.strip().startswith("tests/")]
    assert len(lines) == 10
    assert lines[0] == "tests/test_repo_doctor_strict.py"
    assert lines[-1] == "tests/test_check_repo_alignment_contract.py"
