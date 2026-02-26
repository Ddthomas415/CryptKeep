from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run_make_json(target: str) -> dict:
    out = subprocess.check_output(["make", target], cwd=str(ROOT), text=True)
    return json.loads(out)


def test_make_json_skip_semantics_matrix_smoke():
    p_align = _run_make_json("check-alignment-json-fast")
    guard = p_align.get("guard_tests") or {}
    assert guard.get("skipped") is True
    assert guard.get("rc") == 0

    p_validate = _run_make_json("validate-json-fast")
    s_validate = p_validate.get("steps") or []
    assert isinstance(s_validate, list) and len(s_validate) == 3
    assert s_validate[-1].get("label") == "pytest"
    assert s_validate[-1].get("skipped") is True
    assert s_validate[-1].get("rc") == 0

    p_pre = _run_make_json("pre-release-sanity-json-fast")
    s_pre = p_pre.get("steps") or []
    assert isinstance(s_pre, list) and len(s_pre) == 6
    assert s_pre[-1].get("label") == "pytest"
    assert s_pre[-1].get("skipped") is True
    assert s_pre[-1].get("rc") == 0
