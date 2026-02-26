from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_validate_json_fast_smoke():
    out = subprocess.check_output(
        [sys.executable, str(ROOT / "scripts" / "validate.py"), "--json"],
        cwd=str(ROOT),
        env={**os.environ, "CBP_VALIDATE_SKIP_PYTEST": "1"},
        text=True,
    )
    payload = json.loads(out)
    assert payload.get("schema_version") == 1
    assert payload.get("ok") is True
    assert payload.get("mode") == "full"
    assert payload.get("quick") is False
    assert isinstance(payload.get("started_at"), str) and payload.get("started_at")
    assert isinstance(payload.get("finished_at"), str) and payload.get("finished_at")
    assert isinstance(payload.get("duration_seconds"), (int, float))
    steps = payload.get("steps") or []
    assert isinstance(steps, list) and len(steps) == 3
    assert steps[0].get("label") == "check_repo_alignment"
    assert steps[1].get("label") == "preflight_check"
    assert steps[2].get("label") == "pytest"
    assert steps[2].get("skipped") is True
    assert "CBP_VALIDATE_SKIP_PYTEST" in (steps[2].get("stdout") or "")
