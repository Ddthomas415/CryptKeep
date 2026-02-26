from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_make_check_alignment_list_json_smoke():
    out = subprocess.check_output(["make", "check-alignment-list-json"], cwd=str(ROOT), text=True)
    payload = json.loads(out)
    assert payload.get("schema_version") == 1
    assert payload.get("mode") == "list-tests"
    assert payload.get("ok") is True
    assert isinstance(payload.get("started_at"), str) and payload.get("started_at")
    assert isinstance(payload.get("finished_at"), str) and payload.get("finished_at")
    assert isinstance(payload.get("duration_seconds"), (int, float))
    assert payload.get("duration_seconds") >= 0
    tests = payload.get("guard_tests") or []
    assert isinstance(tests, list)
    assert len(tests) > 0
    assert tests[0] == "tests/test_repo_doctor_strict.py"
    assert tests[-1] == "tests/test_check_repo_alignment_contract.py"
