from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_make_pre_release_sanity_json_fast_smoke():
    out = subprocess.check_output(["make", "pre-release-sanity-json-fast"], cwd=str(ROOT), text=True)
    payload = json.loads(out)
    assert payload.get("schema_version") == 1
    assert payload.get("mode") == "custom"
    assert payload.get("ok") is True
    assert isinstance(payload.get("started_at"), str) and payload.get("started_at")
    assert isinstance(payload.get("finished_at"), str) and payload.get("finished_at")
    assert isinstance(payload.get("duration_seconds"), (int, float))
    steps = payload.get("steps") or []
    assert isinstance(steps, list) and len(steps) == 6
    assert steps[0].get("label") == "alignment_gate"
    assert steps[1].get("label") == "ruff" and steps[1].get("skipped") is True
    assert steps[2].get("label") == "mypy" and steps[2].get("skipped") is True
    assert steps[-1].get("label") == "pytest"
    assert steps[-1].get("rc") == 0
    assert steps[-1].get("skipped") is True
    assert "CBP_PRE_RELEASE_SKIP_PYTEST" in (steps[-1].get("stdout") or "")
