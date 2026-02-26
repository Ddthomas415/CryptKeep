from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_make_validate_json_quick_smoke():
    out = subprocess.check_output(["make", "validate-json-quick"], cwd=str(ROOT), text=True)
    payload = json.loads(out)
    assert payload.get("schema_version") == 1
    assert payload.get("ok") is True
    assert payload.get("mode") == "quick"
    assert payload.get("quick") is True
    assert isinstance(payload.get("started_at"), str) and payload.get("started_at")
    assert isinstance(payload.get("finished_at"), str) and payload.get("finished_at")
    assert isinstance(payload.get("duration_seconds"), (int, float))
    assert payload.get("duration_seconds") >= 0
    steps = payload.get("steps") or []
    assert len(steps) == 2
