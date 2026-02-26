from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run_make_json(target: str) -> dict:
    out = subprocess.check_output(["make", target], cwd=str(ROOT), text=True)
    return json.loads(out)


def test_make_json_quick_semantics_matrix_smoke():
    p_list = _run_make_json("check-alignment-list-json")
    assert p_list.get("mode") == "list-tests"
    tests = p_list.get("guard_tests") or []
    assert isinstance(tests, list) and len(tests) > 0

    p_validate_quick = _run_make_json("validate-json-quick")
    s_v = p_validate_quick.get("steps") or []
    assert p_validate_quick.get("mode") == "quick"
    assert p_validate_quick.get("quick") is True
    assert isinstance(s_v, list) and len(s_v) == 2
    assert s_v[0].get("label") == "check_repo_alignment"
    assert s_v[1].get("label") == "pytest_quick"
    assert s_v[1].get("rc") == 0
    assert s_v[1].get("skipped") is None

    p_pre_quick = _run_make_json("pre-release-sanity-json-quick")
    s_p = p_pre_quick.get("steps") or []
    assert p_pre_quick.get("mode") == "quick"
    assert isinstance(s_p, list) and len(s_p) == 6
    assert s_p[0].get("label") == "alignment_gate"
    assert s_p[0].get("rc") == 0
    for i in range(1, 6):
        assert s_p[i].get("skipped") is True
