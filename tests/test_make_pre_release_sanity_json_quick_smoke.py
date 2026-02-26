from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_make_pre_release_sanity_json_quick_smoke():
    out = subprocess.check_output(["make", "pre-release-sanity-json-quick"], cwd=str(ROOT), text=True)
    payload = json.loads(out)
    assert payload.get("schema_version") == 1
    assert payload.get("mode") == "quick"
    assert payload.get("ok") is True
    assert isinstance(payload.get("started_at"), str) and payload.get("started_at")
    assert isinstance(payload.get("finished_at"), str) and payload.get("finished_at")
    assert isinstance(payload.get("duration_seconds"), (int, float))
    assert payload.get("duration_seconds") >= 0
    steps = payload.get("steps") or []
    assert isinstance(steps, list) and len(steps) == 6
    assert steps[0].get("label") == "alignment_gate"
    assert steps[0].get("rc") == 0
    assert steps[1].get("label") == "ruff" and steps[1].get("skipped") is True
    assert steps[2].get("label") == "mypy" and steps[2].get("skipped") is True
    assert steps[3].get("label") == "yaml_config_validation" and steps[3].get("skipped") is True
    assert steps[4].get("label") == "import_smoke" and steps[4].get("skipped") is True
    assert steps[5].get("label") == "pytest" and steps[5].get("skipped") is True
