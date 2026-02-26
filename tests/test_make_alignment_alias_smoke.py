from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run(target: str) -> str:
    return subprocess.check_output(["make", target], cwd=str(ROOT), text=True)


def test_make_alignment_alias_smoke():
    out_alias = _run("alignment")
    out_direct = _run("check-alignment")
    assert "[alignment] OK" in out_alias
    assert "[alignment] OK" in out_direct
