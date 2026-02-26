from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_make_check_alignment_json_fast_smoke():
    out = subprocess.check_output(["make", "check-alignment-json-fast"], cwd=str(ROOT), text=True)
    payload = json.loads(out)
    assert payload.get("schema_version") == 1
    assert payload.get("mode") == "full_skip_guards"
    assert payload.get("ok") is True
    assert isinstance(payload.get("started_at"), str) and payload.get("started_at")
    assert isinstance(payload.get("finished_at"), str) and payload.get("finished_at")
    assert isinstance(payload.get("duration_seconds"), (int, float))
    assert payload.get("duration_seconds") >= 0
    guard = payload.get("guard_tests") or {}
    tests = payload.get("tests") or []
    assert isinstance(tests, list) and len(tests) > 0
    assert guard.get("count") == len(tests)
    assert guard.get("skipped") is True
